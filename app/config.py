# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str  # Obligatorio, debe estar en tu .env
    db_path: str = "/app/data/ai_butler.db"    # Ruta absoluta DENTRO del contenedor Docker
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

