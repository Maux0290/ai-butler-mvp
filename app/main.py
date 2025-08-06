# app/main.py

import logging
import sentry_sdk
import os
from fastapi import FastAPI, HTTPException, Depends, Form, Request, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from httpx import HTTPError, RequestError
from jose import jwt
from datetime import datetime, timedelta

from .utils import hash_password, verify_password
from .auth import get_current_user, require_admin
from .config import settings
from .db import get_db, Base, engine
from .models import User, Conversation as ConversationModel  # SQLAlchemy models
from .schemas import (
    Conversation as ConversationSchema,  # Pydantic model
    UserCreate, UserAdminCreate, UserOut, QAQuery
)
from .chains import qa_chain, chain
from .crud import (
    create_user, create_user_admin, get_users, update_user_role,
    create_conversation, get_conversations, get_conversation_by_id
)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from sqlalchemy.orm import Session

# -------- 1. Inicializa logging avanzado --------

LOG_FILENAME = "ai_butler.log"

file_handler = logging.FileHandler(LOG_FILENAME, encoding="utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(stream_handler)

for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access", "ai_butler", "fastapi", "root"):
    log = logging.getLogger(logger_name)
    log.setLevel(logging.INFO)
    log.addHandler(file_handler)
    log.addHandler(stream_handler)

logger = logging.getLogger("ai_butler")
logger.info("AI Butler API iniciada con logging centralizado y Sentry.")

# -------- 2. Inicializa Sentry --------
sentry_sdk.init(
    dsn="https://c1c0778ed2b9b9976199067c3893523b@o4509769652240384.ingest.de.sentry.io/4509769655189584",
    traces_sample_rate=1.0,
    environment="production",   # Cambia a "production" en despliegue real
)

# -------- 3. Inicializa la base de datos (solo para desarrollo, en prod usa Alembic) --------
Base.metadata.create_all(bind=engine)
IS_TESTING = os.getenv("TESTING", "0") == "1"
DEFAULT_LIMITS = ["1000/minute"] if IS_TESTING else ["5/minute"]

limiter = Limiter(key_func=get_remote_address, default_limits=DEFAULT_LIMITS)
# -------- 4. Inicializa la app y el limitador de velocidad --------
app = FastAPI(
    title="AI-Butler MVP con RAG",
    version="0.1.0",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# -------- 5. Handler global de excepciones HTTP --------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTPException en {request.method} {request.url.path}: {exc.status_code} {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# -------- 6. Handler global para excepciones no gestionadas --------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Excepción no gestionada en {request.method} {request.url.path}: {repr(exc)}")
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error de servidor. Ya ha sido reportado a soporte."}
    )

# -------- 7. Modelos de petición/entrada --------
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# -------- 8. Endpoints --------

@app.get("/", tags=["default"])
async def health_check():
    """Health check simple."""
    return {"status": "OK"}

@app.get("/force-error/")
async def force_error():
    """Endpoint para forzar un error y probar logging/Sentry."""
    logger.info("Fuerza un error para probar logs y Sentry")
    raise ValueError("Error forzado para probar logs")

# -------- 8.1 Autenticación y registro --------


@app.post("/register/", response_model=UserOut)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registro público: crea usuario SIEMPRE con rol 'user'.
    """
    hashed = hash_password(user.password)
    try:
        db_user = create_user(
            db,
            user,      # Pasamos directamente el modelo UserCreate
            hashed     # No se pasa role, la función lo forza internamente
        )
        return UserOut.from_orm(db_user)
    except ValueError as e:
        logger.error(f"Error en registro: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login/", response_model=TokenOut)
#@limiter.limit("5/minute")
@limiter.limit("1000/minute")  # Relaja el límite para pruebas, cambia a "5/minute" en producción
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Login de usuario. Devuelve un JWT.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}

# -------- 8.2 Endpoints solo para administradores --------

@app.post("/admin/create-user/", response_model=UserOut, dependencies=[Depends(require_admin)], tags=["admin"])
async def admin_create_user(user: UserAdminCreate, db: Session = Depends(get_db)):
    """
    Solo un admin puede crear usuarios con cualquier rol ('user' o 'admin').
    Integra crud.create_user_admin.
    """
    hashed = hash_password(user.password)
    try:
        db_user = create_user_admin(db, user, hashed)
        return UserOut.from_orm(db_user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.patch("/admin/users/{user_id}/role/", response_model=UserOut, dependencies=[Depends(require_admin)], tags=["admin"])
async def change_user_role(user_id: int = Path(..., gt=0), new_role: str = Form(...), db: Session = Depends(get_db)):
    """
    Cambia el rol de un usuario existente ('user' <-> 'admin'). Solo admins pueden hacerlo.
    Integra crud.update_user_role.
    """
    try:
        user = update_user_role(db, user_id, new_role)
        return UserOut.from_orm(user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/usuarios/", tags=["admin"], response_model=list[UserOut], dependencies=[Depends(require_admin)])
async def listar_usuarios(db: Session = Depends(get_db)):
    """
    Listar todos los usuarios (solo admins).
    Integra crud.get_users.
    """
    users = get_users(db)
    return [UserOut.from_orm(u) for u in users]

# -------- 8.3 Endpoints para usuarios autenticados --------

@app.get("/perfil/")
async def profile(current_user: dict = Depends(get_current_user)):
    """Solo usuarios autenticados pueden acceder."""
    return {
        "msg": f"Bienvenido {current_user['username']}. Tu rol es: {current_user['role']}"
    }

@app.get("/mi-perfil/", tags=["usuarios"])
async def mi_perfil(current_user: dict = Depends(get_current_user)):
    """Devuelve los datos del usuario autenticado."""
    return {
        "msg": f"Bienvenido {current_user['username']}",
        "role": current_user['role']
    }

# -------- 8.4 Endpoints de conversación --------

@app.post("/ask-rag/", tags=["default"])
@limiter.limit("30/minute")
async def ask_rag(
    request: Request,
    payload: QAQuery,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Usa RAG para responder y guarda la conversación asociada al usuario autenticado.
    Integra crud.create_conversation.
    """
    try:
        # answer = await qa_chain.arun({...})
        answer = "respuesta de ejemplo"
        conv = create_conversation(
            db, business=payload.business, question=payload.question, answer=answer, user_id=current_user["id"]
        )
        return {"answer": answer}
    except Exception as e:
        logger.exception(f"Error inesperado en /ask-rag/: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor."
        )

@app.get("/conversations/", response_model=list[ConversationSchema], tags=["conversations"])
async def list_conversations(db: Session = Depends(get_db)):
    """
    Devuelve todas las conversaciones grabadas, ordenadas por fecha.
    Integra crud.get_conversations.
    """
    conversations = get_conversations(db)
    return [ConversationSchema.from_orm(c) for c in conversations]

@app.get("/conversations/{conversation_id}/", response_model=ConversationSchema, tags=["conversations"])
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """
    Recupera una conversación por su ID.
    Integra crud.get_conversation_by_id.
    """
    conv = get_conversation_by_id(db, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationSchema.from_orm(conv)

# -------- 8.5 Endpoint consulta simple sin RAG --------

@app.get("/ask/", tags=["default"])
async def ask_simple(business: str, question: str):
    """
    Consulta simple sin RAG.
    """
    try:
        answer = chain.run({"business": business, "question": question})
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Error en /ask/: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# -------- 9. Static files y plantillas web --------

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.get("/web/", response_class=HTMLResponse)
async def render_form(request: Request):
    """Renderiza el formulario web."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask-web/", response_class=HTMLResponse)
async def ask_from_web(request: Request, business: str = Form(...), question: str = Form(...)):
    """
    Procesa preguntas desde el formulario web.
    """
    try:
        result = await qa_chain.arun({
            "business": business,
            "question": question
        })
        return templates.TemplateResponse("index.html", {
            "request": request,
            "answer": result
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "answer": f"Error: {str(e)}"
        })

