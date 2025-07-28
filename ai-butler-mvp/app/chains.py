# app/chains.py

from langchain_openai import OpenAI                # Adaptador oficial de OpenAI para LangChain
from langchain import PromptTemplate, LLMChain     # Plantillas e hilo de inferencia
from .config import settings                       # Tu objeto settings con la API key

# 1) Definimos el prompt que usará el LLM
template = """
Eres un asistente experto en negocios.
Negocio: {business}
Pregunta: {question}
Respuesta:
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["business", "question"]
)

# 2) Instanciamos el LLM pasando la clave desde settings
llm = OpenAI(
    openai_api_key=settings.openai_api_key,
    temperature=0
)

# 3) Creamos la cadena principal de inferencia
chain = LLMChain(
    llm=llm,
    prompt=prompt
)

# 4) Exportamos un alias explícito para main.py
qa_chain = chain



