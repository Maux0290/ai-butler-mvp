# app/exceptions.py

class ExternalServiceError(Exception):
    """Error al comunicarse con un servicio externo (OpenAI)."""

class ValidationError(Exception):
    """Error de validación de datos de entrada."""
