
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.pipeline_model import Pipeline
from backend.service.graph_service import isDag

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get('/')
def read_root():
    return {'Ping': 'Pong'}


@app.post('/pipelines/parse')
def parse_pipeline(pipeline: Pipeline):
    boolDag = isDag(pipeline)
    return {'num_nodes': len(pipeline.nodes), 'num_edges': len(pipeline.edges), 'is_dag': boolDag}
