from collections import deque ,defaultdict
from models.pipeline_model import Pipeline

def isDag(pipeline):
    nodes = pipeline.nodes;
    edges = pipeline.edges;

    adjacency = defaultdict(list)
    indegree = defaultdict(int)

    for node in nodes:
        indegree[node['id']] = 0;

    for edge in edges:
        adjacency[edge['source']].append(edge['target'])
        indegree[edge['target']] += 1;
    node_order = []
    queue = deque()
    for node in indegree:
        if indegree[node] == 0:
            queue.append(node)
            node_order.append(node)
    
    visCount = 0;
    while queue:
        currNode = queue.popleft()
        visCount += 1
        for neighbor in adjacency[currNode]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                node_order.append(neighbor)
                queue.append(neighbor)
    
    boolDag = (visCount == len(nodes))
    return {"isDag" : boolDag,"executionOrder": node_order}




