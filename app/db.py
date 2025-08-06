# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

# Motor de conexión: lee la DATABASE_URL del .env (PostgreSQL)
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Sesión local para usar en endpoints FastAPI (usa 'autocommit' y 'autoflush' a False para seguridad)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base para definir los modelos
Base = declarative_base()

# Dependencia para obtener una sesión de DB por petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

