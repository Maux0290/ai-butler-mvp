from pydantic import BaseModel
from datetime import datetime

class Conversation(BaseModel):
    id: int
    business: str
    question: str
    answer: str
    created_at: datetime