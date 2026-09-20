from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class GraphPlan:
    is_dag: bool
    levels: list[list[str]]
    order: list[str]


def build_graph_plan(nodes: list[dict], edges: list[dict]) -> GraphPlan:
    """Return Kahn execution levels; nodes in each level are independent."""
    node_ids = [node["id"] for node in nodes]
    indegree = {node_id: 0 for node_id in node_ids}
    adjacency: dict[str, list[str]] = defaultdict(list)

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if source not in indegree or target not in indegree:
            return GraphPlan(False, [], [])
        adjacency[source].append(target)
        indegree[target] += 1

    current_level = [node_id for node_id in node_ids if indegree[node_id] == 0]
    levels: list[list[str]] = []
    order: list[str] = []

    while current_level:
        levels.append(current_level)
        order.extend(current_level)
        next_level: list[str] = []
        for node_id in current_level:
            for target in adjacency[node_id]:
                indegree[target] -= 1
                if indegree[target] == 0:
                    next_level.append(target)
        current_level = next_level

    return GraphPlan(len(order) == len(node_ids), levels, order)
