from pathlib import Path
from app.vectorstore import build_vectorstore
from langchain.docstore.document import Document
from app.config import settings


def load_faqs(faqs_path: Path) -> list[Document]:
    """
    Lee faqs.txt y devuelve lista de Document cada uno con pregunta\nrespuesta.
    """
    docs = []
    with open(faqs_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip() or ";" not in line:
                continue
            q, a = line.strip().split(";", 1)
            docs.append(Document(page_content=q + "\n" + a))
    return docs


def main():
    base = Path(__file__).parent.parent
    faqs_path = base / "faqs.txt"
    if not faqs_path.exists():
        print(f"❌ No se encontró {faqs_path}")
        return

    docs = load_faqs(faqs_path)
    store = build_vectorstore(docs, settings.openai_api_key)
    print(f"✅ Índice FAISS generado en {base / 'faiss_index'}")

if __name__ == "__main__":
    main()