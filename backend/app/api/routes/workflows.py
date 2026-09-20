from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.core.security import SecurityConfigurationError, verify_access_token
from app.db import DatabaseUnavailable
from app.db import workflows
from app.models.pipeline import Pipeline
from app.services.pipeline import execute_pipeline

router = APIRouter(prefix="/workflows", tags=["workflows"])
bearer = HTTPBearer(auto_error=False)


class SaveWorkflowRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    pipeline: Pipeline


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict[str, Any]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in to access saved workflows.")
    try:
        return verify_access_token(credentials.credentials)
    except (SecurityConfigurationError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def _database_error(exc: DatabaseUnavailable) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("", status_code=status.HTTP_201_CREATED)
def save_workflow(request: SaveWorkflowRequest, user: dict = Depends(current_user)) -> dict:
    try:
        workflow = workflows.save(user_id=user["sub"], name=request.name, definition=request.pipeline.model_dump())
        return {"status": "success", "workflow": workflow}
    except DatabaseUnavailable as exc:
        raise _database_error(exc) from exc


@router.get("")
def list_workflows(user: dict = Depends(current_user)) -> dict:
    try:
        return {"status": "success", "workflows": workflows.list_for_user(user["sub"])}
    except DatabaseUnavailable as exc:
        raise _database_error(exc) from exc


@router.get("/{workflow_id}")
def get_workflow(workflow_id: str, user: dict = Depends(current_user)) -> dict:
    try:
        workflow = workflows.get_for_user(workflow_id=workflow_id, user_id=user["sub"])
    except DatabaseUnavailable as exc:
        raise _database_error(exc) from exc
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
    return {"status": "success", "workflow": workflow}


@router.post("/{workflow_id}/run")
def run_workflow(workflow_id: str, user: dict = Depends(current_user)) -> dict:
    try:
        workflow = workflows.get_for_user(workflow_id=workflow_id, user_id=user["sub"])
    except DatabaseUnavailable as exc:
        raise _database_error(exc) from exc
    if workflow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
    return {"workflow": {key: value for key, value in workflow.items() if key != "definition"}, **execute_pipeline(Pipeline.model_validate(workflow["definition"]))}
