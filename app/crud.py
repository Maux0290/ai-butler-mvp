# app/crud.py

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from .models import User, Conversation
from .schemas import UserCreate, UserAdminCreate, QAQuery

# --------- USUARIOS ---------

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import User
from .schemas import UserCreate, UserAdminCreate

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .models import User
from .schemas import UserCreate, UserAdminCreate

def create_user(db: Session, user: UserCreate, hashed_password: str) -> User:
    """
    Crea un usuario estándar (siempre con rol 'user').
    No acepta nunca un campo 'role' del input, solo crea users normales.
    """
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role="user"  # Blindado: siempre será 'user'
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Usuario o email ya existe")

def create_user_admin(db: Session, user: UserAdminCreate, hashed_password: str) -> User:
    """
    Crea un usuario con cualquier rol (solo debe usarse en endpoints protegidos).
    El rol lo elige el admin, así que se toma del esquema UserAdminCreate.
    """
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=user.role  # Aquí sí se permite admin/user (pero solo desde endpoint protegido)
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise ValueError("Usuario o email ya existe")


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()

def update_user_role(db: Session, user_id: int, new_role: str) -> User:
    """
    Cambia el rol de un usuario ('user' <-> 'admin').
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("Usuario no encontrado")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user

# --------- CONVERSACIONES ---------

def create_conversation(
    db: Session, business: str, question: str, answer: str, user_id: Optional[int] = None
) -> Conversation:
    """
    Crea y guarda una conversación.
    """
    conv = Conversation(
        business=business,
        question=question,
        answer=answer,
        user_id=user_id
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

def get_conversations(db: Session, skip: int = 0, limit: int = 100) -> List[Conversation]:
    """
    Devuelve todas las conversaciones, ordenadas por fecha de creación descendente.
    """
    return db.query(Conversation).order_by(Conversation.created_at.desc()).offset(skip).limit(limit).all()

def get_conversation_by_id(db: Session, conv_id: int) -> Optional[Conversation]:
    """
    Devuelve una conversación por su ID.
    """
    return db.query(Conversation).filter(Conversation.id == conv_id).first()

def get_conversations_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Conversation]:
    """
    Devuelve todas las conversaciones de un usuario.
    """
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).offset(skip).limit(limit).all()

def delete_conversation(db: Session, conv_id: int) -> bool:
    """
    Elimina una conversación por su ID.
    """
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        return False
    db.delete(conv)
    db.commit()
    return True

# --------- EXTRAS: Búsqueda y filtros ---------

def search_conversations(db: Session, term: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
    """
    Busca conversaciones por término en pregunta o respuesta.
    """
    return (
        db.query(Conversation)
        .filter(
            (Conversation.question.ilike(f"%{term}%")) |
            (Conversation.answer.ilike(f"%{term}%"))
        )
        .order_by(Conversation.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
