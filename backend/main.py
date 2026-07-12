
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.pipeline_model import Pipeline
from service.executor_service import execute_pipeline

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
    res = execute_pipeline(pipeline)
    return {
        "status": res.get("status","error"),
        "results": res.get("results", []),
        "log": res.get("log", [])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
