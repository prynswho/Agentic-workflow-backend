from collections import deque ,defaultdict
from models.pipeline_model import Pipeline

def isDag(pipeline):
    nodes = pipeline.nodes
    edges = pipeline.edges

    adjacency = defaultdict(list)
    indegree = defaultdict(int)

    for node in nodes:
        indegree[node['id']] = 0

    for edge in edges:
        adjacency[edge['source']].append(edge['target'])
        indegree[edge['target']] += 1

    # Kahn levels guarantee that every node in a level has all of its source
    # nodes in earlier levels.  In particular, a customOutput node cannot run
    # until the node connected to it has completed.  Starting with every root
    # also handles disconnected DAG components.
    current_level = [node_id for node_id, degree in indegree.items() if degree == 0]
    node_order = []
    levels = []

    while current_level:
        levels.append(current_level)
        node_order.extend(current_level)
        next_level = []

        for node_id in current_level:
            for neighbor in adjacency[node_id]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    next_level.append(neighbor)

        current_level = next_level

    return {
        "isDag": len(node_order) == len(nodes),
        "executionOrder": node_order,
        "level_traversals": levels,
    }
