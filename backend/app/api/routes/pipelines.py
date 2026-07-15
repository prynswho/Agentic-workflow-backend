from fastapi import APIRouter
from app.models.pipeline import Pipeline
from app.services.executor_service import execute_pipeline

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post('/parse')
def parse_pipeline(pipeline: Pipeline):
    res = execute_pipeline(pipeline)
    return {
        "status": res.get("status","error"),
        "results": res.get("results", []),
        "log": res.get("log", [])
    }
