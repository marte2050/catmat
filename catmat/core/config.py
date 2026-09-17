from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+asyncpg://root:root@localhost:5432/catmat"

    compras_api_base_url: str = "https://dadosabertos.compras.gov.br/modulo-material/"
    ingestion_page_size: int = 500
    ingestion_concurrency: int = 1
    ingestion_request_interval: float = 0.5
    ingestion_batch_size: int = 1000
    http_timeout: float = 60.0
    http_retries: int = 8
    http_backoff_base: float = 1.0
    http_backoff_max: float = 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
