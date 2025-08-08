# app/config.py

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Clave de OpenAI (si usas integración con IA)
    OPENAI_API_KEY: str

    # Clave secreta para firmar JWT y sesiones
    SECRET_KEY: str

    # Algoritmo de encriptación para JWT (ej: 'HS256')
    ALGORITHM: str

    # Tiempo de expiración del access token JWT (en minutos)
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # Usuario de la base de datos Postgres
    POSTGRES_USER: str

    # Contraseña de la base de datos Postgres
    POSTGRES_PASSWORD: str

    # Nombre de la base de datos Postgres
    POSTGRES_DB: str

    # URL completa de conexión a la base de datos
    DATABASE_URL: str

    class Config:
        env_file = ".env"    # Todas las variables se leen desde este archivo

# Instancia global de settings para usar en toda la app
settings = Settings()

# --- Ejemplo de acceso rápido ---
if __name__ == "__main__":
    print("DATABASE_URL:", settings.DATABASE_URL)
    print("OPENAI_API_KEY:", settings.OPENAI_API_KEY)
    print("SECRET_KEY:", settings.SECRET_KEY)
    print("ALGORITHM:", settings.ALGORITHM)
    print("ACCESS_TOKEN_EXPIRE_MINUTES:", settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    print("POSTGRES_USER:", settings.POSTGRES_USER)
    print("POSTGRES_DB:", settings.POSTGRES_DB)
    print("POSTGRES_PASSWORD:", settings.POSTGRES_PASSWORD)


