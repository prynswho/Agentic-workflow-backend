from models.pipeline_model import Pipeline
from service.graph_service import isDag
from tools.dummy_executors import NODE_EXECUTORS
# from routers.create_folder_router import run_create_folder
# from routers.output_router import run_output


MAX_RETRY = 2


"""
    Find every edge pointing INTO this node, and pull the already-computed
    result of whatever upstream node produced it.
    Returns a dict keyed by targetHandle (or source id, if no handle given).
    """
def build_input(node_id ,edges,results):
    inputs = {}
    for edge in edges:
        if(edge['target'] != node_id):
            continue
        source_id = edge['source']
        handle_key = edge.get('targetHandle') or source_id
        inputs[handle_key] = results[source_id]
    return inputs

def execute_pipeline(pipeline):
    dag_result = isDag(pipeline)
    nodes = pipeline.nodes;
    edges = pipeline.edges;
    if not dag_result['isDag']:
        return {
            "status": "error",
            "message": "The pipeline contains a cycle and cannot be executed."
        }
    
    node_order = dag_result['executionOrder']
    nodes_by_id = {node['id'] :node for node in nodes}
    results = {};
    log = []
    for node_id in node_order:
        inputs = build_input(node_id ,edges,results);
        node = nodes_by_id[node_id]
        node_type = node.get('type')
        executor = NODE_EXECUTORS.get(node_type)
        if executor is None:
            log.append({"node":node_id ,"status":"skipped", "reason":f"failed execution for the node {node_type} because no executor was found."})
            continue

        data = node.get('data',{}) or {}

        last_error = None
        for attempt in range(0,MAX_RETRY):
            try:
                output = executor(inputs,data)
                results[node_id] = output
                log.append({"node":node_id,"status":"success", "output":output})
                break
            except Exception as e:
                last_error = e
                log.append({"node":node_id,"status":"failed","error":str(e)})
        else:
            log.append({"node":node_id,"status":"failed","reason":f"failed execution for the node {node_type} after {MAX_RETRY} attempts."})
            return {
                "status":"failed",
                "error":last_error,
                "message":"node failed to execute"
            }
    return {
        "status": "success",
        "results": results,
        "log": log
    }
            





    
