import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate";
MODEL = "qwen2.5-coder:7b"
MAX_TOOL_ROUNDS = 5;

TOOL_SYSTEM_PROMPT = """
You are an agent that can use tools to help complete tasks.
When you want to use a tool, respond ONLY with a JSON object in this exact format and nothing else:

{"tool": "create_folder", "args": {"path": "relative/path/here"}}
{"tool": "write_file", "args": {"path": "relative/path/here", "content": "file content here"}}
{"tool": "none", "message": "your normal text response here"}

Rules:
- Never include any text outside the JSON object
- Always use relative paths, never absolute paths
- Use the "none" tool when you have a normal text response
"""



def parse_tool_response(raw_text: str) -> dict:
    # strip markdown code fences if model wrapped response in them
    cleaned = re.sub(r'```(?:json)?\s*|\s*```', '', raw_text).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # model didn't follow format — treat as plain text
        return {"tool": "none", "message": raw_text}

