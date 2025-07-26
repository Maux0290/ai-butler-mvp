from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from .config import OPENAI_API_KEY
from .vectorstore import load_vectorstore

# Carga el vectorstore
vectorstore = load_vectorstore(OPENAI_API_KEY)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

llm = OpenAI(temperature=0.0, openai_api_key=OPENAI_API_KEY)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)



