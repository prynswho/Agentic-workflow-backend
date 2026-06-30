from models.llm_request_model import llmRequest
import requests
from fastapi import FastAPI


app = FastAPI()


def run_llm(request :llmRequest):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json = {
            "model":"config model name",
            "prompt": request.prompt,
            "system": request.system,
            "stream": False
        },
    )

    data = response.json()
    return {"output":data.get("response","")}