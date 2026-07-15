import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:

    open_router_api_key: str = os.getenv("OPEN_ROUTER_API_KEY","key")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY","")
    base_url: str = os.getenv("BASE_URL","")
    flash_base_url: str = os.getenv("BASE_URL_FLASH_2.5","")
    model_llama: str = os.getenv("MODEL_LLAMA","")
    model_gemini: str = os.getenv("MODEL_GEMINI","")
    model_poolside: str = os.getenv("MODEL_POOLSIDE","")
    model: str = os.getenv("MODEL","")
    # os.getenv returns a str; ensure ttl_seconds is an int with a safe default
    ttl_seconds: int = int(os.getenv("ttl_sec", "3600"))
    model_check:str = os.getenv("MODEL_CHECK","")
    postgres_host: str = os.getenv("POSTGRES_HOST","")
    postgres_port: str = os.getenv("POSTGRES_PORT","5432")
    postgres_db: str = os.getenv("POSTGRES_DB","postgres")
    postgres_user: str = os.getenv("POSTGRES_USER","postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD","")

settings = Settings()