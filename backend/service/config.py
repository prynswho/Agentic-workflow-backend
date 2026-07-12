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

settings = Settings()