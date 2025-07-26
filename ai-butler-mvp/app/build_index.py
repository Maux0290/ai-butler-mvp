from pathlib import Path
from app.vectorstore import build_vectorstore  # ya actualizado
from langchain.docstore.document import Document
from app.config import OPENAI_API_KEY

# ... (load_faqs idéntico)

def main():
    base = Path(__file__).parent.parent
    faqs_path = base / "faqs.txt"
    if not faqs_path.exists():
        print(f"❌ No se encontró {faqs_path}")
        return

    print("📖 Cargando FAQs...")
    docs = load_faqs(faqs_path)

    print(f"🔨 Construyendo índice FAISS con {len(docs)} documentos...")
    store = build_vectorstore(docs, OPENAI_API_KEY)

    print(f"✅ Índice FAISS generado y guardado en disco.")
    print(f"   → {base / 'faiss_index'}")

if __name__ == "__main__":
    main()

