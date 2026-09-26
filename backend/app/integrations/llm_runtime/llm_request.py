from pydantic import BaseModel

class llmRequest(BaseModel):
    prompt: str
    system: str = ""
