from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .chains import chain

app = FastAPI(title="AI-Butler MVP")

class Query(BaseModel):
    business: str
    question: str

@app.post("/ask/")
async def ask(payload: Query):
    try:
        # Usa `arun` en lugar de apredict
        answer: str = await chain.arun(
            business=payload.business,
            question=payload.question
        )
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

