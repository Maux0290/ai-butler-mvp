# app/main.py

import sqlite3
import logging.config
import yaml
from fastapi import FastAPI, HTTPException, Depends, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from httpx import HTTPError, RequestError                      # <— sustituye a openai.error
from .utils import hash_password, verify_password              # Funciones de hashing
from jose import jwt                                          # Librería JWT
from datetime import datetime, timedelta
from .auth import get_current_user, require_admin     # Importa las dependencias
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


from .schemas import Conversation, UserCreate, UserOut, QAQuery
from .config import settings
from .db import get_connection, init_db, create_users_table, save_conversation, fetch_all_conversations, fetch_conversation_by_id, add_user_id_to_conversations
from .chains import qa_chain, chain
from .utils import hash_password      # from .exceptions import ExternalServiceError    # opcional, si ya no lo usas puedes comentarlo
import logging
import sentry_sdk


# --------- 1. Inicializa logging ANTES DE TODO ---------

# --------- 3. Inicializa base de datos ---------
init_db()
create_users_table()
add_user_id_to_conversations()

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

logger = logging.getLogger("ai_butler")  # Usamos siempre este logger por convención
logger.info("AI Butler API iniciada con logging centralizado y Sentry.")

# Inicializa Sentry si lo usas
sentry_sdk.init(
    dsn="https://c1c0778ed2b9b9976199067c3893523b@o4509769652240384.ingest.de.sentry.io/4509769655189584",
    traces_sample_rate=1.0,
    environment="development",
)
logger.info("AI Butler API iniciada con logging centralizado y Sentry.")
# --------- 4. Crea la app ---------
app = FastAPI(
    title="AI-Butler MVP con RAG",
    version="0.1.0",
)

# --- Inicialización del limitador ---
limiter = Limiter(key_func=get_remote_address)

# --- Inicialización de FastAPI ---
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --------- 5. Handler global de excepciones ---------
# Handler para HTTPException que loguea errores de FastAPI
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTPException en {request.method} {request.url.path}: {exc.status_code} {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# --- 4. Handler global de errores (solo uno, centraliza todo) ---
# ------ Handler global para cualquier otra excepción no gestionada ------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Excepción no gestionada en {request.method} {request.url.path}: {repr(exc)}")
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error de servidor. Ya ha sido reportado a soporte."}
    )
# --------- 6. Modelo ejemplo de petición ---------
class QAQuery(BaseModel):
    business: str
    question: str

# ------ Endpoint de ejemplo para probar errores ------
@app.get("/force-error/")
async def force_error():
    logger.info("Fuerza un error para probar logs y Sentry")
    raise ValueError("Error forzado para probar logs")


# Endpoint protegido: solo usuarios autenticados pueden ver su perfil
@app.get("/perfil/")
async def profile(current_user: dict = Depends(get_current_user)):
    """
    Solo usuarios autenticados pueden acceder a este endpoint.
    """
    return {
        "msg": f"Bienvenido {current_user['username']}. Tu rol es: {current_user['role']}"
    }

# Endpoint solo para administradores
@app.get("/admin/solo/")
async def admin_only(current_user: dict = Depends(require_admin)):
    """
    Solo usuarios con rol admin pueden acceder a este endpoint.
    """
    return {
        "msg": f"Hola, admin {current_user['username']}!"
    }

# Endpoint protegido: cualquier usuario logueado
@app.get("/mi-perfil/", tags=["usuarios"])
async def mi_perfil(current_user: dict = Depends(get_current_user)):
    """
    Retorna datos del usuario autenticado.
    """
    return {
        "msg": f"Bienvenido {current_user['username']}",
        "role": current_user['role']
    }

# Endpoint protegido solo para admins
@app.get("/admin/configuracion/", tags=["admin"])
async def configuracion_admin(current_user: dict = Depends(require_admin)):
    """
    Solo accesible para usuarios con rol 'admin'.
    """
    return {
        "msg": f"¡Hola, administrador {current_user['username']}!"
    }

@app.get("/", tags=["default"])
async def health_check():
    return {"status": "OK"}

# Registro de usuario
@app.post("/register/", response_model=UserOut)
async def register(user: UserCreate):
    """
    Registra un nuevo usuario con los datos dados en el modelo UserCreate.
    Si no se especifica un rol, el valor por defecto es 'user'.
    """
    conn = get_connection()                         # Abre una conexión a la base de datos
    cur = conn.cursor()                             # Crea un cursor para ejecutar sentencias SQL
    hashed = hash_password(user.password)           # Hashea la contraseña antes de guardarla
    try:
        # Inserta el nuevo usuario, usando el rol enviado (o 'user' si es None)
        cur.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (user.username, user.email, hashed, user.role)
        )
        conn.commit()                              # Guarda cambios en la base de datos
        user_id = cur.lastrowid                    # Obtiene el id generado automáticamente para el usuario
        # Recupera los datos completos del usuario recién creado
        cur.execute("SELECT id, username, email, role, created_at FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        # Convierte los resultados a un diccionario y luego a un modelo Pydantic para la respuesta
        return UserOut(**dict(zip([desc[0] for desc in cur.description], row)))
    except sqlite3.IntegrityError:
        # Si el username o email ya existen, retorna error 400
        raise HTTPException(status_code=400, detail="Usuario o email ya existe")
    finally:
        conn.close()                              # Siempre cierra la conexión, aunque haya error

# Modelo para la respuesta del login (token JWT)
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Endpoint de login: devuelve JWT
@app.post("/login/", response_model=TokenOut)
@limiter.limit("5/minute")# Solo 5 logins por minuto por IP
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    conn = get_connection()                                   # Conexión a la BD
    cur = conn.cursor()
    # Busca usuario por username
    cur.execute("SELECT id, username, email, password_hash, role, created_at FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    if not row:
        # Si no encuentra el usuario, responde error 401
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    user = dict(zip([desc[0] for desc in cur.description], row))  # Convierte resultado en dict
    # Verifica contraseña enviada contra el hash almacenado
    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    # Prepara los datos a incluir en el JWT
    data = {
        "sub": str(user["id"]),                               # sub: subject = ID de usuario
        "username": user["username"],                         # username
        "role": user["role"],                                 # role: user/admin
        "exp": datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)  # expiración
    }
    # Genera el JWT firmado
    token = jwt.encode(data, settings.secret_key, algorithm=settings.algorithm)
    # Devuelve el token y el tipo de token (bearer)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/ask-rag/", tags=["default"])
@limiter.limit("30/minute")
async def ask_rag(
    request: Request,
    payload: QAQuery,
    current_user: dict = Depends(get_current_user)
):
    """
    Crea una conversación asociada al usuario autenticado.
    """
    try:
        # answer = await qa_chain.arun({ ... })    # <--- tu lógica real
        # save_conversation(...)
        # return {"answer": answer}
        raise ValueError("Error forzado para probar logs")  # <-- descomenta para probar error real

    except (HTTPError, RequestError) as e:
        logger.error(f"Error HTTP en /ask-rag/: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=502,
            detail="Error al comunicarse con el servicio de IA, inténtalo más tarde."
        )
    except Exception as e:
        logger.exception(f"Error inesperado en /ask-rag/: {str(e)}")
        raise  # Esto lo atrapará el handler global y lo enviará también a Sentry y al log


@app.get("/usuarios/", tags=["admin"], response_model=list[UserOut])
async def listar_usuarios(current_user: dict = Depends(require_admin)):
    """
    Permite a los administradores listar todos los usuarios registrados.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, role, created_at FROM users")
    rows = cur.fetchall()
    conn.close()
    # Construye lista de UserOut usando los campos de la tabla
    return [UserOut(**dict(zip([desc[0] for desc in cur.description], row))) for row in rows]

@app.post("/ask-rag/", tags=["default"])
async def ask_rag(payload: QAQuery):
    """
    Pregunta con RAG: usa qa_chain para obtener respuesta
    """
    try:
        # Usamos .arun (devuelve directamente string)
        answer: str = await qa_chain.arun({
            "business": payload.business,
            "question": payload.question
        })

        # Guardamos conversación
        save_conversation(payload.business, payload.question, answer)
        return {"answer": answer}

    except (HTTPError, RequestError):
        # Errores de red / HTTP al llamar a OpenAI
        raise HTTPException(
            status_code=502,
            detail="Error al comunicarse con el servicio de IA, inténtalo más tarde."
        )
    except OpenAIError as e:
        # Capturamos cualquier excepción de la librería OpenAI
        # p.ej. RateLimitError, APIError, etc.
        raise HTTPException(
            status_code=503,
            detail=f"Servicio de IA no disponible: {e}"
        )
    except Exception as e:
        # Cualquier otra excepción
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor."
        )

@app.get("/ask/", tags=["default"])
async def ask_simple(business: str, question: str):
    """
    Consulta simple sin RAG: ejecuta chain directo
    """
    try:
        answer = chain.run({"business": business, "question": question})
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get(
    "/conversations/",
    response_model=list[Conversation],
    tags=["conversations"]
)
async def list_conversations():
    """
    Devuelve todas las conversaciones grabadas, ordenadas por fecha.
    """
    try:
        return fetch_all_conversations()
    except Exception:
        raise HTTPException(status_code=500, detail="Error al leer conversaciones")

@app.get(
    "/conversations/{conversation_id}/",
    response_model=Conversation,
    tags=["conversations"]
)
async def get_conversation(conversation_id: int):
    """
    Recupera una conversación por su ID.
    """
    conv = fetch_conversation_by_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi import Form


app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/web/", response_class=HTMLResponse)
async def render_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/ask-web/", response_class=HTMLResponse)
async def ask_from_web(request: Request, business: str = Form(...), question: str = Form(...)):
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



