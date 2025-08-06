
# app/chains.py

from langchain_openai import ChatOpenAI                # Adaptador de Chat para OpenAI
from langchain.chains import LLMChain                  # Cadena LLM (ruta recomendada)
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate,
)
from .config import settings                            # settings.openai_api_key

# 1) System prompt: rol y tono
system_message = SystemMessagePromptTemplate.from_template(
    "Eres un asistente amable y profesional especializado en {business}, responde con claridad y brevedad."
)

# 2) Few-shot para guiar la generación
examples = [
    {
        "business": "Panadería La Española",
        "question": "¿Cuál es el horario?",
        "answer": "Nuestro horario es de Lunes a Sábado de 8:00 a 14:00."
    },
    {
        "business": "Panadería La Española",
        "question": "¿Aceptan devoluciones?",
        "answer": "Aceptamos devoluciones en un plazo de 30 días con ticket de compra."
    }
]

few_shot_messages = []
for ex in examples:
    # Mensaje humano de ejemplo
    few_shot_messages.append(
        HumanMessagePromptTemplate.from_template(
            "Negocio: {business}\nPregunta: {question}"
        ).format(**ex)  # devuelve HumanMessage
    )
    # Mensaje IA de ejemplo
    few_shot_messages.append(
        AIMessagePromptTemplate.from_template("{answer}").format(**ex)
    )

# 3) Plantilla para la consulta real
human_message = HumanMessagePromptTemplate.from_template(
    "Negocio: {business}\nPregunta: {question}\nRespuesta:"
)

# 4) Ensamblamos el prompt: system + few-shot + human
chat_prompt = ChatPromptTemplate.from_messages(
    [system_message, *few_shot_messages, human_message]
)

# 5) Instanciamos ChatOpenAI
llm = ChatOpenAI(
    openai_api_key=settings.OPENAI_API_KEY,
    temperature=0.2,
    max_tokens=200
)

# 6) Creamos la cadena y la exponemos
chain = LLMChain(llm=llm, prompt=chat_prompt)
qa_chain = chain
