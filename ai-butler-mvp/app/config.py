# app/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Carga la OPENAI_API_KEY desde .env y define el path
    de la base de datos SQLite (ai_butler.db por defecto).
    """
    openai_api_key: str            # Tu clave de OpenAI, obligatoria
    db_path: str = "ai_butler.db"  # Fichero SQLite en /app dentro del contenedor

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instancia global que luego importas en chains.py, db.py, etc.
settings = Settings()

