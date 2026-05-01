from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Anthropic (LLM)
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6"

    # Voyage AI (Embedding)
    voyage_api_key: str
    embedding_model: str = "voyage-3"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: str = ""
    qdrant_url: str = ""  # Cloud URL (優先)

    # Collection names
    race_collection: str = "jra_races"
    horse_collection: str = "jra_horses"

    # JRA-VAN
    jra_van_data_dir: str = "./data/jra_van"

    # App
    app_name: str = "競馬分析AI"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
