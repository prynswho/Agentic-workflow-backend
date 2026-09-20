from typing import Any

from pydantic import BaseModel, Field


class Pipeline(BaseModel):
    """React Flow graph submitted by the frontend."""

    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
