from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "CivicPulse"
    database_url: str = "postgresql+psycopg://civicpulse:change-me@postgres:5432/civicpulse"
    redis_url: str = "redis://redis:6379/0"
    triage_provider: str = "simulated"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_model: str = "llama-3.1-8b-instant"
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "llama3.2:1b"
    rate_limit_requests: int = Field(default=10, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    trust_proxy_headers: bool = False
    log_level: str = "INFO"
    triage_cache_ttl_seconds: int = 86_400
    stats_cache_ttl_seconds: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
