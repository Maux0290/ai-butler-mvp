# app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .schemas import Conversation
from .config import settings
from .db import init_db, save_conversation, fetch_all_conversations, fetch_conversation_by_id
from .chains import qa_chain, chain  # ahora exportamos ambos en chains.py

# 1) Inicializamos la base de datos al arrancar
init_db()

# 2) Creamos la app
app = FastAPI(
    title="AI-Butler MVP con RAG",
    version="0.1.0",
)

# 3) Modelo de petición para RAG
class QAQuery(BaseModel):
    business: str
    question: str

@app.get("/", tags=["default"])
async def health_check():
    return {"status": "OK"}

@app.post("/ask-rag/", tags=["default"])
async def ask_rag(payload: QAQuery):
    # 1) Invocación asíncrona CORRECTA de la cadena
    result = await qa_chain.arun({        # <— usa .arun en lugar de .ainvoke
        "business": payload.business,
        "question": payload.question
    })
    answer = result

    # 2) Guardamos y devolvemos
    save_conversation(payload.business, payload.question, answer)
    return {"answer": answer}

@app.get("/ask/", tags=["default"])
async def ask_simple(business: str, question: str):
    try:
        # Consulta simple sin RAG
        # Ajusta aquí si tu chain espera un dict o solo la pregunta
        answer = chain.run({"business": business, "question": question})
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/", response_model=list[Conversation], tags=["conversations"])
async def list_conversations():
    """
    Devuelve todas las conversaciones grabadas, ordenadas por fecha (más recientes primero).
    """
    try:
        return fetch_all_conversations()
    except Exception:
        raise HTTPException(status_code=500, detail="Error al leer conversaciones")

@app.get("/conversations/{conversation_id}/", response_model=Conversation, tags=["conversations"])
async def get_conversation(conversation_id: int):
    """
    Recupera una conversación específica por su ID.
    """
    conv = fetch_conversation_by_id(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv
  


