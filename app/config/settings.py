from pydantic_settings import BaseSettings
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    openai_api_key: str
    gemini_api_key: str
    xai_api_key: str
    qdrant_api_key: str
    qdrant_url: str
    database_url: str

    embedding_model: str = "gemini-embedding-001"
    gemini_model: str = "gemini-2.5-flash"
    temperature: float = 0.1

    vector_dimension: int = 3072
    qdrant_collection: str = "zoommer_products_hybrid"

    class Config:
        env_file = str(ROOT_DIR / ".env")
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'ignore'

settings = Settings()