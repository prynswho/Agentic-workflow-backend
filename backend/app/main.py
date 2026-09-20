import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.pipelines import router as pipelines_router
from app.api.routes.workflows import router as workflows_router
from app.db import DatabaseUnavailable, database


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Initialize optional auth storage without disrupting local pipelines."""
    try:
        database.initialize()
    except DatabaseUnavailable as exc:
        logging.getLogger(__name__).warning("Auth database was not initialized: %s", exc)
    yield


app = FastAPI(title="Agentic Workflow Pipeline API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(pipelines_router)
app.include_router(auth_router)
app.include_router(workflows_router)


@app.get("/")
def read_root() -> dict:
    return {"Ping": "Pong"}
