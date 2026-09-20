from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.pipeline import Pipeline
from app.services.pipeline import execute_pipeline, resume_pipeline

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]


@router.post("/parse")
def parse_pipeline(pipeline: Pipeline) -> dict:
    """Run a DAG until completion, failure, or a human-approval pause."""
    return execute_pipeline(pipeline)


@router.post("/resume/{run_id}")
def resume_after_approval(run_id: str, approval: ApprovalDecision) -> dict:
    """Resume a paused local-development HITL run."""
    return resume_pipeline(run_id, approval.decision)
