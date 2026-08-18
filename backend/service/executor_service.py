from models.pipeline_model import Pipeline
from service.graph_service import isDag
from tools.dummy_executors import NODE_EXECUTORS
import concurrent.futures
from functools import partial
# from routers.create_folder_router import run_create_folder
# from routers.output_router import run_output


MAX_RETRY = 3


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


def execute_output_node(node_id, edges, completed_outputs):
    """Return the already-computed value from an Output node's source.

    Output nodes are pass-through terminal nodes.  They deliberately copy the
    source value unchanged so callers can look up either the producer node or
    the Output node in the top-level ``results`` map.
    """
    incoming_edge = next(
        (edge for edge in edges if edge.get("target") == node_id),
        None,
    )

    if incoming_edge is None:
        return {
            "status": "error",
            "error": f"Output node '{node_id}' has no incoming edge.",
        }

    source_id = incoming_edge.get("source")
    if source_id not in completed_outputs:
        return {
            "status": "error",
            "error": (
                f"Output node '{node_id}' cannot read source node "
                f"'{source_id}' because it has not completed."
            ),
        }

    return completed_outputs[source_id]


def execute_node(node_id,nodes_by_id,edges,results):
    log = []
    node = nodes_by_id[node_id]
    node_data = node['data']
    node_type = node['type']

    # React Flow emits Output nodes as ``customOutput``.  The DAG scheduler
    # only runs this node after its source has completed, so ``results`` is the
    # completed-node-output map required for this pass-through operation.
    if node_type == "customOutput":
        output = execute_output_node(node_id, edges, results)
        log.append({"node": node_id, "status": output.get("status", "success"), "output": output})
        return {
            "status": "success",
            "results": {node_id: output},
            "log": log,
        }

    node_executor = NODE_EXECUTORS.get(node_type)

    if node_executor is None:
        log.append({"node" : node_id, "status" : "skipped", "reason" : f"failed execution for the node {node_type} because no executor was found"})
        return{
            "status":"failed",
            "error":"no node executor found",
            "message":"no node executor found for the current node",
            "log":log
        }

    last_error = None
    for _ in range(0,MAX_RETRY):
        try:
            inputs = build_input(node_id,edges,results)
            output = node_executor(inputs,node_data)
            log.append({"node" : node_id, "status": "success", "output":output})
            return {
                "status":"success",
                "results":{node_id:output},
                "log":log
            }
        except Exception as e:
            last_error = e
            log.append({"node":node_id,"status":"failed","error":str(e)})

    log.append({"node":node_id,"status":"failed","reason" : f"max retries exceeded as {MAX_RETRY} for the node {node_id}"})
    return{
        "status":"failed",
        "error":last_error,
        "message":"node failed execution",
        "log":log
    }


def execute_pipeline(pipeline):
    dag_result = isDag(pipeline)
    nodes = pipeline.nodes;
    edges = pipeline.edges;
    if not dag_result['isDag']:
        return {
            "status": "error",
            "message": "The pipeline contains a cycle and cannot be executed."
        }
    
    levels = dag_result['level_traversals']
    results = {};
    log = []
    nodes_by_id = {node['id'] : node for node in nodes}

    for curr_level in levels:
        node_fn = partial(execute_node,nodes_by_id=nodes_by_id,edges=edges,results=results)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            temp_res = list(executor.map(node_fn,curr_level))
        
        for res in temp_res:
            log.extend(res['log'])
            if res['status'] == 'failed':
                return {"status":"failed","error":res["error"],"message":res["message"],"log":log}
            results.update(res['results'])
    
    return {
        "status":"success",
        "results":results,
        "log":log
    }
