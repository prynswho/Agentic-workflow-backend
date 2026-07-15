from app.models.llm_request import llmRequest
from app.models.text_request import textRequest
import requests
from openai import OpenAI
from app.core.config import settings


OPEN_ROUTER_API_KEY = settings.open_router_api_key
GEMINI_API_KEY = settings.gemini_api_key
BASE_URL = settings.base_url
BASE_URL_FLASH_2_5 = settings.flash_base_url
MODEL_LAMMA = settings.model_llama
MODEL_GEMINI = settings.model_gemini
MODEL_POOLSIDE= settings.model_poolside
MODEL= settings.model


client = OpenAI(
  base_url=BASE_URL,
  api_key=OPEN_ROUTER_API_KEY,
)

def call_llm(request: llmRequest, stream=False):
    print(client.base_url)
    response = client.chat.completions.create(
        model=MODEL,
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
