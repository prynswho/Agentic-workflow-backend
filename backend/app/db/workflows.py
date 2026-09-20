"""PostgreSQL persistence for user-owned workflow definitions."""

import hashlib
import json
from uuid import uuid4

from psycopg.types.json import Json

from app.db.database import database


def workflow_digest(definition: dict) -> str:
    canonical = json.dumps(definition, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _serialize(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "name": row["name"],
        "digest": row["digest"],
        "definition": row["definition"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
    }


def save(*, user_id: str, name: str, definition: dict) -> dict:
    workflow_id = uuid4()
    digest = workflow_digest(definition)
    with database.connection() as connection:
        row = connection.execute(
            """
            INSERT INTO saved_workflows (id, user_id, name, definition, digest)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, digest, definition, created_at, updated_at
            """,
            (workflow_id, user_id, name.strip(), Json(definition), digest),
        ).fetchone()
    return _serialize(row)


def list_for_user(user_id: str) -> list[dict]:
    with database.connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, digest, definition, created_at, updated_at
            FROM saved_workflows WHERE user_id = %s ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [_serialize(row) for row in rows]


def get_for_user(*, workflow_id: str, user_id: str) -> dict | None:
    with database.connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, digest, definition, created_at, updated_at
            FROM saved_workflows WHERE id = %s AND user_id = %s
            """,
            (workflow_id, user_id),
        ).fetchone()
    return _serialize(row) if row else None
