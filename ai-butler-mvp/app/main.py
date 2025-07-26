# app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .chains import chain
from .db import init_db, save_conversation

# 1) Inicializamos la BD al arrancar la app
app = FastAPI(title="AI-Butler MVP")
init_db()

class Query(BaseModel):
    business: str
    question: str

@app.get("/")
async def health_check():
    return {"status": "OK"}

@app.post("/ask/")
async def ask(payload: Query):
    try:
        # 2) Ejecutamos el LLM
        answer: str = await chain.arun(
            business=payload.business,
            question=payload.question
        )
        # 3) Guardamos la interacción en la base de datos
        save_conversation(
            business=payload.business,
            question=payload.question,
            answer=answer
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


