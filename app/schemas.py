# app/schemas.py

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
import re

# --------- Ejemplos personalizados para tu marca ---------
EXAMPLE_USERNAME = "ai-butler_user"
EXAMPLE_EMAIL = "soporte@ai-butler.com"
EXAMPLE_BUSINESS = "TuMejorVersion"
USERNAME_REGEX = r"^[a-zA-Z0-9_.-]{3,30}$"  # Letras, números, _, ., -, 3-30 caracteres

# --------- 1. Esquemas para usuarios ---------

class UserBase(BaseModel):
    username: str = Field(..., example=EXAMPLE_USERNAME, min_length=3, max_length=30)
    email: Optional[EmailStr] = Field(None, example=EXAMPLE_EMAIL)

    @validator('username')
    def username_must_match_regex(cls, v):
        if not re.match(USERNAME_REGEX, v):
            raise ValueError(
                "El nombre de usuario solo puede contener letras, números, guion bajo (_), punto (.) o guion (-), y tener entre 3 y 30 caracteres."
            )
        return v

class UserCreate(UserBase):
    """
    Modelo de registro público de usuario.
    - No incluye 'role', siempre se asigna 'user' en el backend.
    """
    password: str = Field(..., example="ClaveUltraSegura2024!", min_length=8, max_length=60)

    @validator('password')
    def password_strength(cls, v):
        # Validación mínima de seguridad: 8 caracteres, al menos una letra y un número
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra.")
        return v

class UserAdminCreate(UserBase):
    """
    Modelo solo para admins: permite asignar cualquier rol.
    Úsalo en endpoints protegidos.
    """
    password: str = Field(..., example="ClaveUltraSegura2024!", min_length=8, max_length=60)
    role: str = Field("user", example="admin")  # El admin puede crear usuarios admin

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"\d", v):
            raise ValueError("La contraseña debe contener al menos un número.")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra.")
        return v

class UserOut(UserBase):
    """
    Modelo de usuario para respuestas (nunca incluye password).
    Incluye el campo 'role'.
    """
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserWithConversations(UserOut):
    """
    Modelo de usuario que incluye todas sus conversaciones.
    """
    conversations: List['Conversation'] = []

    class Config:
        from_attributes = True


# --------- 2. Esquemas para conversaciones ---------

class Conversation(BaseModel):
    id: int
    business: Optional[str] = Field(None, example=EXAMPLE_BUSINESS, max_length=80)
    question: Optional[str] = Field(None, example="¿Cómo puedo mejorar mi enfoque diario?", max_length=400)
    answer: Optional[str] = Field(None, example="Practica la técnica Pomodoro y elimina distracciones.", max_length=1000)
    created_at: datetime
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


# --------- 3. Esquema de entrada para RAG ---------

class QAQuery(BaseModel):
    business: str = Field(..., example=EXAMPLE_BUSINESS, max_length=80)
    question: str = Field(..., example="¿Cuál es la mejor rutina matinal para aumentar mi productividad?", min_length=5, max_length=400)

    @validator('business')
    def business_no_empty(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("El campo business no puede estar vacío.")
        return v.strip()

# --------- 4. Otros ejemplos de personalización ---------

class Feedback(BaseModel):
    user_id: int = Field(..., example=42)
    message: str = Field(..., example="Me ha encantado la experiencia con AI-Butler.", min_length=10, max_length=500)

    class Config:
        from_attributes = True


# Forward reference para Conversation en UserWithConversations
UserWithConversations.update_forward_refs()


