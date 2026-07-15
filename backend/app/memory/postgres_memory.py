import json
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2 import pool

from app.core.config import settings

_pool = psycopg2.pool.SimpleConnectionPool(
    1,
    10,
    host=settings.postgres_host,
    port=settings.postgres_port,
    dbname=settings.postgres_db,
    user=settings.postgres_user,
    password=settings.postgres_password,
)


@contextmanager
def _get_cursor():
    conn = _pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)


def init_db() -> None:
    "creates the tables if they don't already exist, safe to call on every startup"
    with _get_cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS turns (
                id SERIAL PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_turns_session_id ON turns (session_id, created_at);"
        )


def add_turn(session_id: str, role: str, content: str) -> None:
    "permanently stores a turn, unlike redis this has no TTL/trim"
    with _get_cursor() as cur:
        cur.execute(
            "INSERT INTO turns (session_id, role, content) VALUES (%s, %s, %s);",
            (session_id, role, json.dumps(content) if not isinstance(content, str) else content),
        )


def get_all_turns(session_id: str) -> list[dict]:
    with _get_cursor() as cur:
        cur.execute(
            "SELECT role, content, created_at FROM turns WHERE session_id = %s ORDER BY created_at ASC;",
            (session_id,),
        )
        return [dict(row) for row in cur.fetchall()]


def get_recent_turns(session_id: str, limit: int = 50) -> list[dict]:
    with _get_cursor() as cur:
        cur.execute(
            """
            SELECT role, content, created_at FROM (
                SELECT role, content, created_at FROM turns
                WHERE session_id = %s
                ORDER BY created_at DESC
                LIMIT %s
            ) sub ORDER BY created_at ASC;
            """,
            (session_id, limit),
        )
        return [dict(row) for row in cur.fetchall()]


def clear_session(session_id: str) -> None:
    with _get_cursor() as cur:
        cur.execute("DELETE FROM turns WHERE session_id = %s;", (session_id,))
