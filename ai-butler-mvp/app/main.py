from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Importa tu chain RAG
from .chains import qa_chain  
# Importa tus funciones de base de datos
from .db import init_db, save_conversation  

app = FastAPI(title="AI-Butler MVP con RAG")

# Inicializa la base de datos
init_db()

class QAQuery(BaseModel):
    business: str
    question: str

@app.get("/")
async def health_check():
    return {"status": "OK"}

# ESTE es el endpoint que debes tener:
@app.post("/ask-rag/")
async def ask_rag(payload: QAQuery):
    try:
        # Reemplaza `qa_chain.run(...)` por `await qa_chain.ainvoke(...)`
        # o en síncrono: result = qa_chain.invoke(...)
        result = await qa_chain.ainvoke({"query": payload.question})
        # result es un dict: {"result": "...", "source_documents": [...]}

        answer = result["result"]
        save_conversation(payload.business, payload.question, answer)

        sources = [
            {"content": doc.page_content}
            for doc in result["source_documents"]
        ]
        return {"answer": answer, "sources": sources}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


