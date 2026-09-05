import os
import sys
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")

class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartDoc API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "smartdoc_dev_secret_key_983274982374892374982374"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./smartdoc.db"
    SYNC_DATABASE_URL: str = "sqlite:///./smartdoc.db"
    
    # Storage
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "storage", "uploads")
    
    # LLM Provider Selection ("ollama" or "claude")
    LLM_PROVIDER: str
    
    # Ollama Local Settings
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    OLLAMA_TEMPERATURE: float = 0.1
    
    # Anthropic Claude API Settings
    ANTHROPIC_API_KEY: Optional[str] = ""
    DEFAULT_MODEL: str = "claude-3-5-sonnet-20241022"
    MAP_MODEL: str = "claude-3-haiku-20240307"
    
    # Processing limits & chunking
    MAX_FILE_SIZE_MB: int = 100
    CHUNK_SIZE_TOKENS: int = 1500
    CHUNK_OVERLAP_TOKENS: int = 150
    CHUNK_SIZE_CHARS: int = 4000
    CHUNK_OVERLAP_CHARS: int = 400

    # Ollama execution params
    OLLAMA_TIMEOUT_SECONDS: float = 120.0
    OLLAMA_NUM_PREDICT: int = 1536
    OLLAMA_NUM_CTX: int = 4096

    # Web Search Fallback Settings
    WEB_SEARCH_ENABLED: bool = Field(default=True)
    TAVILY_API_KEY: Optional[str] = Field(default=None)
    TAVILY_MAX_RESULTS: int = 5

    # System & Logging
    LOG_LEVEL: str = "INFO"
    RETRY_ATTEMPTS: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5

    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=env_path,
        extra="ignore"
    )

# Validate .env existence and load settings
if not os.path.exists(env_path):
    raise RuntimeError(
        f"[SmartDoc Startup Configuration Error]: '.env' file not found at {env_path}! "
        f"Please create backend/.env (you can copy backend/.env.example)."
    )

try:
    settings = Settings()
except Exception as err:
    raise RuntimeError(
        f"[SmartDoc Startup Configuration Error]: Required environment variables missing or invalid in '.env'. Details: {err}"
    )

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
