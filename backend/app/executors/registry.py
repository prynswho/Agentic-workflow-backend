from typing import Any


def execute_node(node: dict[str, Any], inputs: dict[str, Any], completed_outputs: dict[str, Any]) -> Any:
    """Dispatch node execution without coupling scheduling to node implementation."""
    node_type = node.get("type")
    data = node.get("data") or {}

    if node_type == "customOutput":
        incoming = next(iter(inputs.values()), None)
        if not inputs:
            return {"status": "error", "error": f"Output node '{node['id']}' has no incoming edge."}
        return incoming

    if node_type == "humanInTheLoop":
        decision = data.get("decision", "pending")
        return {
            "status": "awaiting_approval" if decision == "pending" else "success",
            "prompt": data.get("prompt", "Review this step before continuing."),
            "decision": decision,
            "inputs": inputs,
        }

    if node_type == "customInput":
        return {"status": "success", "results": data.get("value", "")}

    if node_type == "llm":
        # Compatibility boundary: existing model/tool calling behavior remains
        # untouched while scheduling and API code live in the new app package.
        from tools.dummy_executors import llm_node_executor
        return llm_node_executor(inputs, data)

    raise ValueError(f"No executor is registered for node type '{node_type}'.")
