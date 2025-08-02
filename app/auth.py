from fastapi import Depends, HTTPException, status                # Importa utilidades de FastAPI
from fastapi.security import OAuth2PasswordBearer                  # Esquema OAuth2 para obtener el token Bearer
from jose import jwt, JWTError                                     # Funciones para decodificar JWT
from .config import settings                                       # Acceso a configuración (SECRET_KEY, algoritmo)

# Define el esquema OAuth2, usando la ruta /login/ para obtener el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Decodifica el JWT recibido y retorna los datos del usuario autenticado.
    Lanza 401 si el token es inválido o faltan campos clave.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado o token inválido",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica el JWT usando la clave secreta y algoritmo definido en settings
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: str = payload.get("sub")           # subject: ID de usuario
        username: str = payload.get("username")     # nombre de usuario
        role: str = payload.get("role")             # rol del usuario (user/admin)
        # Si falta algún dato esencial, lanza 401
        if user_id is None or username is None or role is None:
            raise credentials_exception
        # Devuelve un diccionario con los datos del usuario autenticado
        return {"id": user_id, "username": username, "role": role}
    except JWTError:
        # Si el token no se puede decodificar o ha expirado, lanza 401
        raise credentials_exception

def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Permite acceso solo si el usuario autenticado tiene rol 'admin'.
    Lanza 403 si el rol es distinto.
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso solo para administradores"
        )
    # Si es admin, permite continuar y retorna los datos del usuario
    return current_user
