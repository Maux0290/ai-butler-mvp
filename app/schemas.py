from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """
    Modelo para registro de usuario.
    Permite enviar el rol ('user' o 'admin'). Por defecto será 'user' si no se especifica.
    """
    username: str                       # Nombre de usuario único
    email: Optional[str] = None         # Email opcional
    password: str                       # Contraseña en texto plano (se hasheará)
    role: Optional[str] = "user"        # Rol del usuario ('user' o 'admin'), por defecto 'user'

class UserOut(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    created_at: datetime

class Conversation(BaseModel):
    id: int
    business: str
    question: str
    answer: str
    created_at: datetime

class QAQuery(BaseModel):
    business: str
    question: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
