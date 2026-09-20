import concurrent.futures
from copy import deepcopy
from time import perf_counter
from typing import Any

from app.core.config import settings
from app.executors import execute_node
from app.models.pipeline import Pipeline
from app.services.graph import build_graph_plan
from app.services.hitl import hitl_store


def _inputs_for(node_id: str, edges: list[dict], outputs: dict[str, Any]) -> dict[str, Any]:
    inputs: dict[str, Any] = {}
    for edge in edges:
        if edge.get("target") != node_id:
            continue
        source = edge.get("source")
        if source not in outputs:
            raise ValueError(f"Source node '{source}' has not completed.")
        inputs[edge.get("targetHandle") or source] = outputs[source]
    return inputs


def _run_one(node_id: str, nodes_by_id: dict[str, dict], edges: list[dict], outputs: dict[str, Any]) -> dict:
    node = nodes_by_id[node_id]
    started = perf_counter()
    try:
        value = execute_node(node, _inputs_for(node_id, edges, outputs), outputs)
        return {"node": node_id, "status": "success", "value": value, "duration_ms": round((perf_counter() - started) * 1000, 2)}
    except Exception as exc:
        return {"node": node_id, "status": "failed", "error": str(exc), "duration_ms": round((perf_counter() - started) * 1000, 2)}


def execute_pipeline(pipeline: Pipeline) -> dict:
    plan = build_graph_plan(pipeline.nodes, pipeline.edges)
    if not plan.is_dag:
        return {"status": "error", "results": {}, "log": [{"status": "error", "message": "The pipeline contains a cycle or an edge referencing an unknown node."}]}

    nodes_by_id = {node["id"]: node for node in pipeline.nodes}
    outputs: dict[str, Any] = {}
    log: list[dict] = []

    for level in plan.levels:
        # Each node sees only completed outputs from earlier levels. The map is
        # updated after all futures complete, preventing shared-state races.
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.max_parallel_nodes) as executor:
            completed = list(executor.map(lambda node_id: _run_one(node_id, nodes_by_id, pipeline.edges, outputs), level))

        for item in completed:
            log.append({key: value for key, value in item.items() if key != "value"})
            if item["status"] == "failed":
                return {"status": "failed", "results": outputs, "log": log, "error": item["error"]}

            outputs[item["node"]] = item["value"]
            value = item["value"]
            if nodes_by_id[item["node"]].get("type") == "humanInTheLoop" and value.get("status") == "awaiting_approval":
                run_id = hitl_store.create(pipeline.model_dump(), item["node"], value["prompt"])
                return {
                    "status": "paused",
                    "results": outputs,
                    "log": log,
                    "pending_approval": {"run_id": run_id, "node_id": item["node"], "prompt": value["prompt"], "options": ["approved", "rejected"]},
                }

    return {"status": "success", "results": outputs, "log": log}


def resume_pipeline(run_id: str, decision: str) -> dict:
    if decision not in {"approved", "rejected"}:
        return {"status": "error", "results": {}, "log": [], "error": "Decision must be 'approved' or 'rejected'."}
    pending = hitl_store.pop(run_id)
    if pending is None:
        return {"status": "error", "results": {}, "log": [], "error": "Approval run was not found or has expired."}

    payload = deepcopy(pending.pipeline)
    for node in payload["nodes"]:
        if node["id"] == pending.node_id:
            node.setdefault("data", {})["decision"] = decision
            break
    return execute_pipeline(Pipeline.model_validate(payload))
