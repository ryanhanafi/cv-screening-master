import os
from django.core.management.base import BaseCommand
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

class Command(BaseCommand):
    help = 'Ingests documents into the vector store'

    def handle(self, *args, **options):
        self.stdout.write("Starting document ingestion...")

        # Load documents
        loader = DirectoryLoader(
            './documents',
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True,
            use_multithreading=True
        )
        documents = loader.load()

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)

        # Get embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

        # Create ChromaDB client and collection
        vector_store = Chroma.from_documents(
            texts,
            embeddings,
            persist_directory="./chroma_db"
        )
        vector_store.persist()

        self.stdout.write(self.style.SUCCESS('Successfully ingested documents.'))
