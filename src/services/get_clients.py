import chromadb
from chromadb import PersistentClient
import logging
logger = logging.getLogger(__name__)
from src.config import get_settings
settings = get_settings()
from sentence_transformers import SentenceTransformer


_chroma_client = None
def get_chroma_client() -> PersistentClient:
    global _chroma_client
    
    if _chroma_client is None:
        logger.info("Initializing ChromaDB Persistent Client...")
        
        _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_FOLDER)
    
    return _chroma_client


_embedding_model = None
def get_embedding_model() -> SentenceTransformer:
    global _embedding_model

    if _embedding_model is None:
        logger.info(f"Loading Embedding Model '{settings.EMBEDDING_MODEL}' into memory... this might take a few seconds.")
        
        _embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)
        logger.info("Embedding Model loaded successfully!")
        
    return _embedding_model