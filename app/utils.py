from passlib.context import CryptContext  # Importa PassLib para manejo seguro de contraseñas

# Configura PassLib para usar bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Genera un hash seguro para la contraseña dada."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña plana corresponde al hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)
