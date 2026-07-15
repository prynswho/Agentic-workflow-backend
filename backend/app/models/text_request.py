from pydantic import BaseModel

class textRequest(BaseModel):
    prompt: str
    system: str = ""
