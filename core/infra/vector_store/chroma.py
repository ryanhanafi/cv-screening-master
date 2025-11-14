from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from core.application.interfaces import IVectorStore

class ChromaVectorStore(IVectorStore):
    def __init__(self, persist_directory="./chroma_db"):
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        self.vector_store = Chroma(persist_directory=persist_directory, embedding_function=self.embeddings)

    def get_retriever(self):
        return self.vector_store.as_retriever()
