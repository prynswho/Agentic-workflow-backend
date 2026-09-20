from dataclasses import dataclass
from threading import Lock
from uuid import uuid4


@dataclass
class PendingRun:
    pipeline: dict
    node_id: str
    prompt: str


class HitlStore:
    """Local-development HITL run store.

    This is intentionally in-memory. Replace it with Redis or a database when
    approvals must survive a backend restart or serve multiple workers.
    """

    def __init__(self) -> None:
        self._runs: dict[str, PendingRun] = {}
        self._lock = Lock()

    def create(self, pipeline: dict, node_id: str, prompt: str) -> str:
        run_id = str(uuid4())
        with self._lock:
            self._runs[run_id] = PendingRun(pipeline, node_id, prompt)
        return run_id

    def pop(self, run_id: str) -> PendingRun | None:
        with self._lock:
            return self._runs.pop(run_id, None)


hitl_store = HitlStore()
