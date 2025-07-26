# app/db.py

import sqlite3
from sqlite3 import Connection
from pathlib import Path

# 1) Definimos la ruta del fichero .db en la raíz del proyecto
BASE_DIR = Path(__file__).parent.parent
DB_PATH = BASE_DIR / "ai_butler.db"

def get_connection() -> Connection:
    """
    Obtiene una conexión a la base de datos SQLite.
    Si la base no existe, la crea automáticamente.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    """
    Inicializa las tablas necesarias si no existen.
    Llamar una sola vez al arrancar la app.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_conversation(business: str, question: str, answer: str):
    """
    Inserta un nuevo registro en la tabla `conversations`.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations (business, question, answer)
        VALUES (?, ?, ?)
    """, (business, question, answer))
    conn.commit()
    conn.close()

