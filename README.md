this is not a very pretty code , as im new to python so i know the file structure is a mess right now

BUT IT WORKS (I will change it in a few days)

to use this code , you will need to 
1.create a venv first

 -> in a .env file
2.configure your api key ( can get it on Open Router)
3.use any models you want , can configure it there
-> nothing else in .env

3.USE PYTHON 3.12=> , as libraries like mcp , uvicorn are not working with 3.14 ( maybe cause its new)

to run the server -> python main.py

==============THIS CODE WILL NOT WORK WITHOUT THE MCP SERVER, SO CHECK OUT THE MCP SERVER REPO FIRST============================

New structure (verified main.py imports and serves the same route, /pipelines/parse):


backend/
  main.py                        # thin entrypoint: FastAPI(), CORS, include_router, uvicorn.run
  app/
    api/routes/pipelines.py      # POST /pipelines/parse (moved out of main.py, now a real APIRouter)
    core/config.py                # was service/config.py
    models/
      pipeline.py                 # was models/pipeline_model.py
      llm_request.py               # was models/llm_request_model.py
      text_request.py              # was models/text_request_model.py
    services/
      executor_service.py
      graph_service.py
      llm_service.py               # tool-calling loop
      llm_client.py                 # was routers/llm_router.py — it's an LLM client, not a router
    tools/
      dummy_executors.py
      mcp_tools.py
    memory/
      redis_memory.py
      postgres_memory.py
      README.md
Dead code removed along the way:

run_text_node / run_llm_node print-stub functions in dummy_executors.py — confirmed unused, deleted.
The stray app = FastAPI() in routers/llm_router.py (now llm_client.py) — a leftover, unused instance.
Unused Pipeline imports in executor_service.py/graph_service.py, unused requests import and dead OLLAMA_URL/MODEL constants in llm_service.py.
Kept, per your correction: run_llm_without_tools in llm_service.py — still unused today but reserved for wiring into text nodes later.

Old flat folders (models/, service/, routers/, tools/, memory/) and stale __pycache__ are deleted. All imports were rewritten to the new app.* paths, and I confirmed python -c "import main" loads cleanly with the same routes as before.