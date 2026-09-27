from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
from functools import lru_cache

class Settings(BaseSettings):
    # Application information
    APP_NAME : str
    APP_VERSION:str
    
    
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