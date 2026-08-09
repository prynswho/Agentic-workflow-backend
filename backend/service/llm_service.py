import requests
import json
import re
from routers.llm_router import run_text, call_llm
from models.llm_request_model import llmRequest
from models.text_request_model import textRequest
from memory.redis_memory import add_turns, set_curr
import logging

OLLAMA_URL = "http://localhost:11434/api/generate";
MODEL = "kimi-k2.7-code:cloud"
MAX_TOOL_ROUNDS = 50
MAX_COMPRESSION_ROUNDS = 2  # fetch_all + none — compression should never need more
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

{"tool": "none", "args": {"message": "your final message or task completion summary here"}}

Critical Rules:
- ALL your responses MUST be a valid JSON object, and ONLY a JSON object. No other text, explanations, or markdown fences () should be included.
- Use relative paths for all file system operations. ABSOLUTE paths are forbidden.
- Your final output for a task MUST use the "none" tool with a clear message.
- If you encounter an error or cannot proceed, use the "none" tool to explain the situation.
"""

CONTEXT_COMPRESSION_PROMPT = """
You are a context-compression agent. Your job: fetch the last conversation
turns for a session and compress them into a concise summary that preserves
key facts, decisions, and open tasks.

Respond ONLY with a single valid JSON object. No markdown, no prose, no
explanations outside the JSON.

Available tools:
{"tool": "fetch_all", "args": {"session_id": "<id>"}}
  -> returns {"result_list": [{"role": "...", "content": "..."}, ...]}

{"tool": "none", "args": {"message": "<compressed summary, or an error explanation>"}}
  -> use this exactly once, as your LAST action, to return the compressed summary

Rules:
- Call fetch_all at most once per task.
- Always finish with "none" — your job is only to produce the summary text,
  not to save it anywhere.
- If fetch_all returns no turns or an error, call none immediately with
  a short explanation.
- Keep the compressed summary under ~150 words unless critical detail
  would be lost.

Example:
User: session_id=abc123
Assistant: {"tool": "fetch_all", "args": {"session_id": "abc123"}}
Tool result: {"result_list": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
Assistant: {"tool": "none", "args": {"message": "User is debugging a Redis TTL issue; agreed to set expire on every write; next step is testing trim behavior."}}
"""

def parse_tool_response(raw_text: str) -> dict:
    cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', raw_text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"tool": "none", "args": {"message": raw_text}}


def run_llm_without_tools(reqObj: textRequest):
    return run_text(reqObj)


def run_llm_with_tools(reqObj: llmRequest, session_id: str) -> dict:
    """Runs the filesystem tool-calling loop AND records the turn history to Redis
    (user prompt in, final answer out) so run_context_compression has something to read."""
    from tools.mcp_tools import execute_tool

    prompt = reqObj.prompt
    system = reqObj.system
    combined_system = f"{system}\n\n{TOOL_SYSTEM_PROMPT}".strip()

    add_turns(session_id, "user", prompt)

    full_prompt = prompt
    tools_results_log = []

    for round in range(MAX_TOOL_ROUNDS + 1):
        logger.info(full_prompt)
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

        if tool_name == "none":
            final_message = parsed_response.get("args", {}).get("message", response_json)
            add_turns(session_id, "assistant", final_message)
            return {
                "status": "success",
                "results": final_message,
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

        full_prompt = (
            f"{full_prompt}\n\n"
            f"Tool '{tool_name}' was called with args {json.dumps(tools_arg)}.\n"
            f"Result: {json.dumps(result)}\n"
            f"Continue with the next step or respond with a final message."
        )

    return {
        "status": "error",
        "results": "Maximum tool rounds reached without a final message.",
        "log": tools_results_log,
        "rounds": MAX_TOOL_ROUNDS
    }


def run_context_compression(session_id: str) -> dict:
    """Runs CONTEXT_COMPRESSION_PROMPT to fetch + summarize a session's turns.
    The LLM only produces the summary text — persisting it to Redis is done
    here in code (deterministic), not left to the model to decide via a tool call."""
    from tools.mcp_tools import execute_tool

    full_prompt = f"session_id={session_id}"

    for round in range(MAX_COMPRESSION_ROUNDS):
        user_req = llmRequest(prompt=full_prompt, system=CONTEXT_COMPRESSION_PROMPT)
        response_json = call_llm(user_req)
        parsed_response = parse_tool_response(response_json)
        tool_name = parsed_response.get("tool")

        if not tool_name:
            return {"status": "error", "results": "Model response was missing a 'tool' field.", "rounds": round}

        if tool_name == "none":
            summary = parsed_response.get("args", {}).get("message", response_json)
            set_curr(session_id, summary) 
            return {
                "status": "success",
                "results": summary,
                "rounds": round
            }

        tools_arg = parsed_response.get("args", {})
        try:
            result = execute_tool(tool_name, tools_arg)
            status = "success"
        except Exception as e:
            result = str(e)
            status = "error"

        full_prompt = (
            f"{full_prompt}\n\n"
            f"Tool '{tool_name}' was called with args {json.dumps(tools_arg)}.\n"
            f"Result: {json.dumps(result)}\n"
            f"Respond with the final 'none' message now."
        )

    return {"status": "error", "results": "Compression did not finish within max rounds.", "rounds": MAX_COMPRESSION_ROUNDS}