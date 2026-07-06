import os

WORKSPACE_ROOT = os.path.abspath("/Users/priyanshu/Desktop/agenticWorkflow/workspace");
def resolve_safe_path(relative_path:str) -> str:
    full = os.path.normpath(os.path.join(WORKSPACE_ROOT, relative_path ))
    if not full.startswith(WORKSPACE_ROOT):
        raise ValueError("Resolved path is outside the workspace root")
    return full

def create_folder(relative_path:str) -> dict:
    full_path = resolve_safe_path(relative_path)
    os.makedirs(full_path, exist_ok=True)
    return {"status":"created","path":full_path}

def write_file(path:str,content:str) -> dict:
    safe = resolve_safe_path(path)
    os.makedirs(os.path.dirname(safe), exist_ok=True)
    with(open(safe,"w") as f):
        f.write(content)
    return {"status":"written","path":safe}

TOOL_REGISTRY = {
    "create_folder":lambda args:create_folder(args["path"]),
    "write_file":lambda args:write_file(args["path"],args["content"])
}

def execute_tool(tool_name, args:dict):
    if tool_name not in TOOL_REGISTRY:
        raise ValueError(f"Tool {tool_name} is not registered.")
    return TOOL_REGISTRY[tool_name](args)
