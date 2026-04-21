from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"

class Settings(BaseSettings):
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "alethian_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60
    
    SERPER_API_KEY: str = ""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    GROBID_URL: str = "http://localhost:8070"
    
    MAX_UPLOAD_SIZE_MB: int = 100
    MAX_DRAGNET_QUERIES: int = 20
    DRAGNET_RATE_LIMIT_RPM: int = 60
    ALLOW_AUTO_REGISTRATION: bool = False  # Set False in production
    
    SIMILARITY_EXACT_THRESHOLD: float = 0.95
    SIMILARITY_SEMANTIC_THRESHOLD: float = 0.85
    SIMILARITY_EXACT_RATIO: float = 0.9  # SequenceMatcher ratio to distinguish exact vs paraphrase
    WEB_MATCH_THRESHOLD: float = 0.15
    SHINGLING_WORDS_PER_PAGE: int = 500
    DRAGNET_QUERY_WORDS: int = 25
    SHINGLING_CHARS_PER_PAGE_ESTIMATE: int = 4000
    SHINGLING_WINDOW_SENTENCES: int = 5
    
    # Content fetcher constants
    FETCHER_WINDOW_SIZE: int = 200        # Words per comparison window for web pages
    FETCHER_WINDOW_STEP: int = 100        # Step size between comparison windows
    FETCHER_TIMEOUT: int = 10             # HTTP timeout for fetching web pages
    SNIPPET_MAX_CHARS: int = 500          # Max chars to store from a web snippet
    MIN_TEXT_LENGTH: int = 50             # Minimum extracted chars to consider a document valid
    MIN_SOURCE_TEXT_LENGTH: int = 20      # Minimum chars for a source text to be worth comparing
    MIN_CHUNK_WORDS: int = 30             # Minimum words for a chunk to be worth searching
    
    # Infrastructure constants  
    GROBID_TIMEOUT: int = 120             # Timeout for Grobid HTTP request in seconds
    OCR_DPI: int = 300                    # DPI for Tesseract OCR image conversion
    EMBEDDING_BATCH_SIZE: int = 64        # Batch size for SentenceTransformer encoding
    SERPER_TIMEOUT: int = 10              # Timeout for Serper API requests
    MAX_DRAGNET_SUSPICIOUS: int = 15      # Max suspicious chunks to send to web search
    
    UPLOAD_DIR: str = ""  # If empty, uses <project_root>/uploads; can be set to a shared volume path

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

settings = Settings()
