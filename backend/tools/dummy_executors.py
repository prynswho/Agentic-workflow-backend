from models.llm_request_model import llmRequest
from models.text_request_model import textRequest
import requests 
from service.llm_service import run_llm_with_tools, run_llm_without_tools
from routers.llm_router import run_text
import uuid

def generate_session_id() -> str:
    return str(uuid.uuid4())

def run_text_node(inputs,data):
    print("this is the text node")
    return data.get("text","")

def run_llm_node(inputs,data):
    print("this is the llm node")
    return f":{inputs}"

def run_create_folder_node(inputs,data):
    print("this is the create folder node")
    return inputs

def run_output_node(inputs,data):
    print("this is the output node")
    return data.get("output","")

def llm_node_executor(inputs: dict, data: dict):
    configured_text = data.get("text", "")
    configured_system = data.get("system","")
    upstream_text = "/n".join([str(val) for val in inputs.values() if val])
    if upstream_text:
        final_prompt = f"Context:\n{upstream_text}\n\nTask:\n{configured_text}"
    else:
        final_prompt = configured_text
    if(configured_text == ""):
       configured_text = "hello there"
    req_obj = llmRequest(prompt=final_prompt, system=configured_system)
    return run_llm_with_tools(req_obj,session_id=generate_session_id())  

def text_node_executor(inputs: dict, data: dict):
    configured_text = data.get("text", "")
    configured_system = data.get("system","youre a helpful assistant")
    upstream_text = "/n".join([str(val) for val in inputs.values() if val])
    if upstream_text:
        final_prompt = f"Context:\n{upstream_text}\n\nTask:\n{configured_text}"
    else:
        final_prompt = configured_text
    if(configured_text == ""):
       configured_text = "hello there"
    req_obj = textRequest(prompt=final_prompt, system=configured_system)
    return run_text(req_obj)

NODE_EXECUTORS = {
    "text" : text_node_executor,
    "llm" : llm_node_executor,
    "create_folder" : run_create_folder_node,
    "output" : run_output_node
}