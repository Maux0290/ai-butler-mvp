# app/chains.py

# 1) Importamos la clase OpenAI desde LangChain para conectarnos al LLM
from langchain import OpenAI
# 2) Importamos LLMChain, que une un LLM con una plantilla de prompt
from langchain.chains import LLMChain
# 3) Importamos PromptTemplate para definir dinámicamente nuestros prompts
from langchain.prompts import PromptTemplate
# 4) Importamos la clave que cargamos en config.py
from .config import OPENAI_API_KEY

# ─────────────────────────────────────────────────────────────────────────────
# 5) Inicializamos el cliente de OpenAI con tu clave
#    - temperature: control de creatividad (0.0 = repetitivo, 1.0 = más variado)
llm = OpenAI(
    temperature=0.2,
    openai_api_key=OPENAI_API_KEY
)

# ─────────────────────────────────────────────────────────────────────────────
# 6) Definimos nuestra plantilla de prompt:
#    - {business} y {question} serán reemplazados en tiempo de ejecución
template = """
Eres el AI-Butler de {business}.
El cliente pregunta: "{question}"
Responde de forma clara, profesional y breve.
"""

# 7) Creamos el PromptTemplate con:
#    - template: el texto base con placeholders
#    - input_variables: lista de nombres para sustituir
prompt = PromptTemplate(
    template=template,
    input_variables=["business", "question"]
)

# ─────────────────────────────────────────────────────────────────────────────
# 8) Unimos LLM + prompt en un LLMChain:
#    - chain.run(params) ejecuta la llamada al modelo
#    - chain.apredict(params) es la versión asíncrona
chain = LLMChain(
    llm=llm,
    prompt=prompt
)

