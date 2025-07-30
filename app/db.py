import os
import sqlite3
from datetime import datetime
from .config import settings
from .schemas import Conversation

# Usa la ruta que viene de settings
DB_PATH = settings.db_path

def get_connection():
    # crea carpeta 'data/' si no existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    # tu DDL habitual, p.ej.:
    conn.execute("""
      CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business TEXT,
        question TEXT,
        answer TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    """)
    conn.commit()
    conn.close()

def save_conversation(business: str, question: str, answer: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO conversations (business, question, answer, created_at) VALUES (?, ?, ?, ?)",
        (business, question, answer, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

def fetch_all_conversations() -> list[Conversation]:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, business, question, answer, created_at FROM conversations ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [Conversation(**dict(row)) for row in rows]

def fetch_conversation_by_id(conv_id: int) -> Conversation | None:
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, business, question, answer, created_at FROM conversations WHERE id = ?",
        (conv_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return Conversation(**dict(row)) if row else None
