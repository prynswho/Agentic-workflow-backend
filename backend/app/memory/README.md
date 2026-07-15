# Memory

This folder has two memory backends. They serve different purposes and are meant to be used together, not as alternatives.

## Redis (`redis_memory.py`) — short-term / working memory

Redis is an in-memory key-value store. Here it's used as a **sliding window buffer** for the current conversation/session:

- Each session's turns are pushed onto a Redis **list** under the key `session:{session_id}:turns` (`rpush`).
- `ltrim` keeps only the most recent `MAX_TURNS_TO_KEEP` (10) turns — older ones fall off automatically.
- `expire` sets a TTL (`settings.ttl_seconds`) on the key, so an idle session's memory disappears on its own.
- `build_prompt` reads the recent turns back out and stitches them into a prompt string for the LLM.

Why Redis for this: it's fast (in-memory), and the TTL/trim behavior gives you automatic cleanup for free — you don't want every ephemeral tool-call/response turn kept forever, and you don't want to hand-write expiry logic. The tradeoff is that data isn't durable — if Redis restarts (and there's no persistence configured), it's gone. That's fine for a rolling context window, but wrong for anything you want to keep.

## Postgres (`postgres_memory.py`) — long-term / durable memory

Postgres is used for **long-term storage** of the same kind of turns, but permanently (no TTL, no trimming):

- `turns` table: `id, session_id, role, content, created_at`.
- `init_db()` creates the table/index if missing — call it once at app startup.
- `add_turn(session_id, role, content)` inserts a row (never expires, never trimmed).
- `get_all_turns(session_id)` / `get_recent_turns(session_id, limit)` read history back out, oldest-first.
- `clear_session(session_id)` deletes a session's rows if you explicitly want to purge history.

### Setup

1. Have a Postgres instance running (local install, Docker, or a managed service).
2. Set env vars (see `service/config.py`):
   - `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
3. Install the driver: `pip install psycopg2-binary`
4. Call `init_db()` once when the app starts (e.g. in `main.py`) to create the table.

### Suggested pattern

Use Redis for the hot path (building the prompt for the *current* turn) and write the same turn to Postgres for durability, e.g.:

```python
from app.memory import redis_memory, postgres_memory

def record_turn(session_id: str, role: str, content: str) -> None:
    redis_memory.add_turns(session_id, role, content)   # fast, rolling window
    postgres_memory.add_turn(session_id, role, content)  # durable, full history
```

That way Redis stays cheap and small, while Postgres accumulates the complete, permanent record you can later mine, audit, or replay.

---

## Adding a vector DB (future work — not implemented here)

This is guidance only. Nothing in this repo currently does embeddings, similarity search, or retrieval — do **not** wire up agentic RAG from this doc; it's just the plan for when that's actually needed.

A vector DB would let you do **semantic search** over past turns/documents (e.g. "find memories similar in meaning to this query"), which plain Postgres text columns can't do on their own.

### Option A: `pgvector` extension on the existing Postgres instance (recommended to start)

Keeps everything in one database — simplest ops story, no new service to run.

1. Install the extension (once per DB): `CREATE EXTENSION IF NOT EXISTS vector;`
   - Requires the Postgres server to have `pgvector` installed (available via most managed Postgres providers, or `apt install postgresql-16-pgvector` / the `pgvector/pgvector` Docker image locally).
2. Add a vector column, e.g.:
   ```sql
   ALTER TABLE turns ADD COLUMN embedding vector(1536); -- dimension must match your embedding model
   ```
3. When storing a turn, also compute an embedding (via an embedding model/API) and store it alongside the row.
4. Query nearest neighbors with a distance operator, e.g.:
   ```sql
   SELECT * FROM turns ORDER BY embedding <-> '[...]' LIMIT 5;
   ```
5. Add an index (e.g. `ivfflat` or `hnsw`) once the table has enough rows, for performance.

Python driver support: `pgvector` (pip package) provides adapters for `psycopg2`/`psycopg`/`asyncpg` so you can pass/read Python lists or numpy arrays directly.

### Option B: Dedicated vector database (Qdrant, Weaviate, Milvus, Pinecone, Chroma, etc.)

Worth it once you outgrow `pgvector` (very large corpora, need for advanced filtering/hybrid search, or a managed service). Adds an extra service/dependency to run and keep in sync with Postgres, so only reach for this if `pgvector` becomes a bottleneck.

### What you'd need before implementing either option

- An embedding model/API to turn text into vectors (dimension must be fixed and consistent).
- A decision on what gets embedded (every turn? summarized sessions? specific documents?).
- A retrieval step in the request flow that queries the vector store and folds results into the prompt — this is the "agentic RAG" part that is explicitly **out of scope** for this doc.
