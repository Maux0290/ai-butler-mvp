# app/main.py

import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from httpx import HTTPError, RequestError
from openai import OpenAIError                       # <— sustituye a openai.error

from .schemas import Conversation
from .config import settings
from .db import init_db, save_conversation, fetch_all_conversations, fetch_conversation_by_id
from .chains import qa_chain, chain
# from .exceptions import ExternalServiceError       # opcional, si ya no lo usas puedes comentarlo

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
