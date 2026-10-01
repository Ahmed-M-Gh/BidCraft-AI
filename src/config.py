from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
from functools import lru_cache

class Settings(BaseSettings):
    # Application information
    APP_NAME : str
    APP_VERSION:str
    
    # Reading files settings
    TEMP_DIR : Path = Path(__file__).resolve().parent.parent/"temp_uploads"
    PARTITION_STRATEGY:str = "hi_res"
    
    # Embeddings
    EMBEDDING_MODEL:str = "BAAI/bge-large-en-v1.5"
    # Chroma DB
    CHROMA_DB_FOLDER : Path = Path(__file__).resolve().parent.parent/"asset"/"chroma_db"
    COLLECTION_NAME:str = "company_knowledge_base"
    
    
    # .env file
    model_config = SettingsConfigDict(
        env_file=BASE_DIR/".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Caching the function
@lru_cache
def get_settings() -> Settings:
    return Settings()