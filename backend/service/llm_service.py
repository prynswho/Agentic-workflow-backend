import requests
import json
import re
from routers.llm_router import run_llm, run_text
from models.llm_request_model import llmRequest
from models.text_request_model import textRequest


OLLAMA_URL = "http://localhost:11434/api/generate";
MODEL = "qwen2.5-coder:7b"
MAX_TOOL_ROUNDS = 5;

TOOL_SYSTEM_PROMPT = """
You are an AI agent designed to assist with tasks using available tools. To invoke a tool, respond with a JSON command following this exact format and structure:

{"tool": "create_folder", "args": {"path": "relative/path/here"}}
{"tool": "write_file", "args": {"path": "relative/path/here", "content": "file content here"}}
{"tool": "edit_replace_file", "args": {"path": "relative/path/here", "old_content": "text to replace", "new_content": "replacement text"}}
{"tool": "edit_file", "args": {"path": "relative/path/here", "new_content": "updated file content here"}}
{"tool": "read_file", "args": {"path": "relative/path/here"}}
{"tool": "none", "message": "your normal text response here"}

Adhere to these rules:
- Your responses should always be in JSON format.
- Use relative paths for file operations.
- Employ the 'none' tool for any non-tool related responses."""



def parse_tool_response(raw_text: str) -> dict:
    # strip markdown code fences if model wrapped response in them
    cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', raw_text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # model didn't follow format — treat as plain text
        return {"tool": "none", "message": raw_text}
    

def run_llm_without_tools(reqObj:textRequest):
    # "no tool support needed maybe use it for testnodes and stuff"
    return run_text(reqObj)

def run_llm_with_tools(reqObj: llmRequest) -> dict:
    # system prompt contains tool instructions
    from tools.filesystem_tools import execute_tool

    prompt = reqObj.prompt
    system = reqObj.system
    combined_system = f"{system}\n\n{TOOL_SYSTEM_PROMPT}".strip()

    full_prompt = prompt
    tools_results_log = []

    for round in range(MAX_TOOL_ROUNDS + 1):

        user_req = llmRequest(prompt=full_prompt, system=combined_system)
        response_json = run_llm(user_req, MODEL).get("response", "")
        parsed_response = parse_tool_response(response_json)
        tool_name = parsed_response.get("tool")

        if(tool_name == "none"):
            # model has finished using tools, return final message
            return {
                "status": "success",
                "results": parsed_response.get("message", response_json),
                "log": tools_results_log,
                "rounds": round
            }
        tools_arg = parsed_response.get("args", {})
        try:
            result = execute_tool(tool_name, tools_arg)
            status = "success"
        except Exception as e:
            result = str(e)
            status = "error"
        tools_results_log.append({
            "tool": tool_name,
            "args": tools_arg,
            "result": result,
            "status": status,
            "round": round
        })

         # feed result back into the next prompt so model knows what happened
        full_prompt = (
            f"{full_prompt}\n\n"
            f"Tool '{tool_name}' was called with args {json.dumps(tools_arg)}.\n"
            f"Result: {json.dumps(result)}\n"
            f"Continue with the next step or respond with a final message."
        )
    
    return{
        "status": "error",
        "results": "Maximum tool rounds reached without a final message.",
        "log": tools_results_log,
        "rounds": MAX_TOOL_ROUNDS
    }

