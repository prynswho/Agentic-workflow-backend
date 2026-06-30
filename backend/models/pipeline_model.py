from typing import Optional
from pydantic import BaseModel



class Node(BaseModel):
    id: str
    type: Optional[str] = None
    data: Optional[dict] = None #maybe later on use and bind the pipeline model to just accept nodes but right now its loseley coupled  

class Edge(BaseModel):
    id:Optional[str] = None
    source: str
    target: str
    sourceHandle:Optional[str] = None
    sourceTarget:Optional[str] = None

class Pipeline(BaseModel):
    nodes: list[dict]
    edges: list[dict]




    '''
    nodes = [
    {"id": "text-1", "type": "text", "data": {"text": "hello"}},
    {"id": "llm-1", "type": "llm", "data": {}},
    {"id": "output-1", "type": "customOutput", "data": {}},
    ]

    edges = [
        {"id": "e1", "source": "text-1", "target": "llm-1"},
        {"id": "e2", "source": "llm-1", "target": "output-1"},
    ] 
    '''
