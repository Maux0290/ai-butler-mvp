# app/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # --- Seguridad y autenticación ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Integraciones externas ---
    OPENAI_API_KEY: Optional[str] = None

    # --- Base de datos ---
    DATABASE_URL: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    class Config:
        env_file = ".env"
        case_sensitive = True

    def assemble_db_url(self) -> str:
        """
        Devuelve una DATABASE_URL lista para usar.
        - Si está definida DATABASE_URL → la usa directamente.
        - Si no, construye una desde los parámetros POSTGRES_*.
        """
        if self.DATABASE_URL:
            return self.DATABASE_URL

        if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_DB:
            return (
                f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

        raise ValueError("❌ No se encontró configuración de base de datos válida.")


# Instancia global de configuración
settings = Settings()
DATABASE_URL = settings.assemble_db_url()

# --- Ejemplo de acceso rápido ---
if __name__ == "__main__":
    print("✅ DATABASE_URL:", DATABASE_URL)
    print("🔑 SECRET_KEY:", settings.SECRET_KEY)
    print("⚙️ ALGORITHM:", settings.ALGORITHM)
    print("⏳ ACCESS_TOKEN_EXPIRE_MINUTES:", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    print("🐘 POSTGRES_USER:", settings.POSTGRES_USER)
    print("📂 POSTGRES_DB:", settings.POSTGRES_DB)
