import os
from dataclasses import dataclass

@dataclass
class Settings:

    open_router_api_key: str = os.getenv("OPEN_ROUTER_API_KEY","")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY","")
    base_url: str = os.getenv("BASE_URL","")
    flash_base_url: str = os.getenv("BASE_URL_FLASH_2.5","")
    model_llama: str = os.getenv("MODEL_LLAMA","")
    model_gemini: str = os.getenv("MODEL_GEMINI","")
    model_poolside: str = os.getenv("MODEL_POOLSIDE","")
    model: str = os.getenv("MODEL","")
    # os.getenv returns a str; ensure ttl_seconds is an int with a safe default
    ttl_seconds: int = int(os.getenv("ttl_sec", "3600"))

    # Postgres (long-term memory) settings
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "agentic_workflow")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")


settings = Settings()
