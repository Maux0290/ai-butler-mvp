from pathlib import Path
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings

BASE_DIR = Path(__file__).parent.parent
INDEX_DIR = BASE_DIR / "faiss_index"


def build_vectorstore(docs: list, openai_api_key: str) -> FAISS:
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    store = FAISS.from_documents(docs, embeddings)
    INDEX_DIR.mkdir(exist_ok=True)
    store.save_local(str(INDEX_DIR))
    return store


def load_vectorstore(openai_api_key: str) -> FAISS:
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    return FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True
    )