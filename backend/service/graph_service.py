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
    levels = bfs(nodes,edges,adjacency,node_order[0])['level_traversals']
    return {"isDag" : boolDag,"executionOrder": node_order,'level_traversals':levels}



def bfs(nodes,edges,adjacency_list,start_node):
   
    for edge in edges:
        adjacency_list[edge['source']].append(edge['target'])
    vis = {node['id'] : False for node in nodes}
    vis[start_node] = True;
    q = deque()
    q.append(start_node)
    levels = []
    while q:
        curr_len = len(q)
        curr_level = []
        for _ in range(curr_len):
            curr_node = q.popleft()
            curr_level.append(curr_node)

            for adj_node in adjacency_list[curr_node]:
                if not vis[adj_node]:
                    q.append(adj_node)
                    vis[adj_node] = True
        levels.append(curr_level)
    
    return {"level_traversals" : levels}



        

