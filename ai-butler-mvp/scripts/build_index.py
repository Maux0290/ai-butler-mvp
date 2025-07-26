# scripts/build_index.py

from app.vectorstore import build_vectorstore
from langchain.docstore.document import Document
import os

# 1) Lee tu fuente de datos (aquí faqs.txt)
faqs_path = os.path.join(os.getcwd(), "faqs.txt")
docs = []
with open(faqs_path, encoding="utf-8") as f:
    for line in f:
        question, answer = line.strip().split(";", 1)
        docs.append(Document(page_content=question + "\n" + answer))

# 2) Construye y guarda el índice
from app.config import OPENAI_API_KEY
build_vectorstore(docs, OPENAI_API_KEY)
print("Índice FAISS generado.")

