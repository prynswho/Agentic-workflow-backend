import json
import re
import logging
from app.services.llm_client import run_text,call_llm
from app.models.llm_request import llmRequest
from app.models.text_request import textRequest



MAX_TOOL_ROUNDS = 50;
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOOL_SYSTEM_PROMPT = """
You are an expert autonomous agent designed to complete tasks by effectively using available tools.

Your primary mode of interaction is to respond *exclusively* with a JSON object.

When a task requires interacting with the file system or other external resources, you MUST use one of the provided tools. Structure your tool calls as follows:

{"tool": "tool_name", "args": {"arg1": "value1", "arg2": "value2"}}

Available Tools and their JSON structures:

{"tool": "create_folder", "args": {"path": "relative/path/here"}}
{"tool": "write_file", "args": {"path": "relative/path/here", "content": "file content here"}}
{"tool": "edit_replace_file", "args": {"path": "relative/path/here", "old_content": "text to replace", "new_content": "replacement text"}}
{"tool": "edit_file", "args": {"path": "relative/path/here", "new_content": "updated file content here"}}
{"tool": "read_file", "args": {"path": "relative/path/here"}}
{"tool": "list_files", "args": {"path": "relative/path/here"}}


When you have successfully completed the task, or if you determine that no further tool actions are needed, you MUST return your final answer or message using the "none" tool:

{"tool": "none", "message": "your final message or task completion summary here"}

Critical Rules:
- ALL your responses MUST be a valid JSON object, and ONLY a JSON object. No other text, explanations, or markdown fences () should be included.
- Use relative paths for all file system operations. ABSOLUTE paths are forbidden.
- Your final output for a task MUST use the "none" tool with a clear message.
- If you encounter an error or cannot proceed, use the "none" tool to explain the situation.
"""



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
    from app.tools.mcp_tools import execute_tool

    prompt = reqObj.prompt
    system = reqObj.system
    combined_system = f"{system}\n\n{TOOL_SYSTEM_PROMPT}".strip()

    full_prompt = prompt
    tools_results_log = []

    for round in range(MAX_TOOL_ROUNDS + 1):
        logger.info(full_prompt);
        user_req = llmRequest(prompt=full_prompt, system=combined_system)
        response_json = call_llm(user_req)
        parsed_response = parse_tool_response(response_json)
        tool_name = parsed_response.get("tool")
        if not tool_name:
            return {
                "status": "error",
                "results": "Model response was missing a 'tool' field.",
                "log": tools_results_log,
                "rounds": round
            }
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
