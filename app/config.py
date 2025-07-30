# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    db_path: str = "data/ai_butler.db"    # <<— antes era "./ai_butler.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

