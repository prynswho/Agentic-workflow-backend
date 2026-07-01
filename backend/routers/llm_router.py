from models.llm_request_model import llmRequest
from models.text_request_model import textRequest
import requests
from fastapi import FastAPI


app = FastAPI()


def run_llm(request: llmRequest):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen2.5-coder:7b", 
            "prompt": request.prompt,
            "system": request.system,
            "stream": False
        },
    )

    data = response.json()
    return {"output": data.get("response", "")}
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
