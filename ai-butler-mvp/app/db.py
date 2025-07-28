import sqlite3
from datetime import datetime
from .config import settings
from .schemas import Conversation

DB_PATH = settings.db_path

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Reconstruye la tabla de conversaciones con el campo created_at.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Borrar versión antigua
    cursor.execute("DROP TABLE IF EXISTS conversations;")

    # 2) Crear tabla nueva
    cursor.execute("""
    CREATE TABLE conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)

    conn.commit()
    cursor.close()
    conn.close()


def save_conversation(business: str, question: str, answer: str):
    """Guarda una conversación con timestamp en ISO 8601."""
    conn = get_connection()
    ts = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO conversations (business, question, answer, created_at) VALUES (?, ?, ?, ?)",
        (business, question, answer, ts)
    )
    conn.commit()
    conn.close()


def fetch_all_conversations() -> list[Conversation]:
    """Recupera todas las conversaciones ordenadas de más reciente a más antiguo."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, business, question, answer, created_at FROM conversations ORDER BY created_at DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    return [
        Conversation(
            id=row["id"],
            business=row["business"],
            question=row["question"],
            answer=row["answer"],
            created_at=datetime.fromisoformat(row["created_at"])
        )
        for row in rows
    ]


def fetch_conversation_by_id(conv_id: int) -> Conversation | None:
    """Recupera una conversación por su ID."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, business, question, answer, created_at FROM conversations WHERE id = ?",
        (conv_id,)
    )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return Conversation(
        id=row["id"],
        business=row["business"],
        question=row["question"],
        answer=row["answer"],
        created_at=datetime.fromisoformat(row["created_at"])
    )