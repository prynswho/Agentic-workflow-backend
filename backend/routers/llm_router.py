from models.llm_request_model import llmRequest
from models.text_request_model import textRequest
import requests
from fastapi import FastAPI
from openai import OpenAI
from service.config import settings


app = FastAPI()


# def run_llm(request: llmRequest,Model,stream=False):
#     response = requests.post(
#         "http://localhost:11434/api/generate",
#         json={
#             # "model": "kimi-k2.7-code:cloud", 
#             "model":Model,
#             "prompt": request.prompt,
#             "system": request.system,
#             "stream": False
#         },
#     )

#     return response.json()


OPEN_ROUTER_API_KEY = settings.open_router_api_key
GEMINI_API_KEY = settings.gemini_api_key
BASE_URL = settings.base_url
BASE_URL_FLASH_2_5 = settings.flash_base_url
MODEL_LAMMA = settings.model_llama
MODEL_GEMINI = settings.model_gemini
MODEL_POOLSIDE= settings.model_poolside
MODEL= settings.model
MODEL_CHECK = settings.model_check

client = OpenAI(
  base_url=BASE_URL,
  api_key=OPEN_ROUTER_API_KEY,
)

def call_llm(request: llmRequest, stream=False):
    response = client.chat.completions.create(
        model=MODEL_POOLSIDE,
        messages=[
            {"role": "system", "content": request.system},
            {"role": "user",   "content": request.prompt}
        ],
    extra_body={"reasoning": {"enabled": True}}
    )
    return response.choices[0].message.content or ""



def run_text(request: textRequest):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5-coder:1.5b-instruct",  
            "prompt": request.prompt,
            "system": request.system,
            "stream": False
        },
    )
    
    data = response.json()
    return {"output": data.get("response", "")}
