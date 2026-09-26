import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent
import json

MCP_SERVER_URL = "http://localhost:8000/mcp"

async def _call_tool_async(tool_name:str,args:dict) -> dict:
    async with streamable_http_client(MCP_SERVER_URL) as (read,write, _):
        async with ClientSession(read,write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name,arguments=args)

            for block in result.content:
                if isinstance(block,TextContent):
                    try:
                        return json.loads(block.text)
                    except json.JSONDecodeError:
                        return {"status":"success","result":block.text}
            
            return {"status": "error","message":"no content"}

def execute_tool(tool_name:str,args:dict) -> dict:
    return asyncio.run(_call_tool_async(tool_name,args))