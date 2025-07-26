import os
from dotenv import load_dotenv

# 1) Carga variables de .env en os.environ
#    Calcula la ruta al .env en la raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # carpeta ai-butler-mvp/
dotenv_path = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path)

# 2) Lee directamente la variable de entorno
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 3) Valida que exista, o lanza un error claro
if not OPENAI_API_KEY:
    raise RuntimeError(
        "La variable OPENAI_API_KEY no está definida. "
        "Revisa tu archivo .env en la raíz de ai-butler-mvp."
    )

