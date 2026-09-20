"""Minimal PostgreSQL access and schema setup for account data."""

import logging
from contextlib import contextmanager
from collections.abc import Iterator
from typing import Any

import psycopg
from psycopg.rows import dict_row

from app.core.config import settings

logger = logging.getLogger(__name__)


class DatabaseUnavailable(RuntimeError):
    """The auth database is not configured or cannot be reached."""


class Database:
    def _url(self) -> str:
        url = settings.resolved_database_url
        if not url:
            raise DatabaseUnavailable(
                "PostgreSQL is not configured. Set DATABASE_URL or POSTGRES_PASSWORD and POSTGRES_* values."
            )
        return url

    @contextmanager
    def connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        try:
            # State the row generic on Connection so Pylance understands that
            # dict_row returns dictionaries rather than Psycopg's tuple rows.
            with psycopg.Connection[dict[str, Any]].connect(
                self._url(), row_factory=dict_row, autocommit=True
            ) as connection:
                yield connection
        except DatabaseUnavailable:
            raise
        except psycopg.IntegrityError:
            # Repositories need to distinguish conflicts such as a duplicate
            # email from an unavailable database.
            raise
        except psycopg.Error as exc:
            raise DatabaseUnavailable("The PostgreSQL authentication database is unavailable.") from exc

    def initialize(self) -> None:
        """Create only the account table required by the auth endpoints."""
        with self.connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_users (
                    id UUID PRIMARY KEY,
                    username VARCHAR(100),
                    email VARCHAR(320) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    security_string_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Allows a local database created by the previous development
            # schema to gain display-name support without being recreated.
            connection.execute("ALTER TABLE app_users ADD COLUMN IF NOT EXISTS username VARCHAR(100)")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS app_users_email_idx ON app_users (email)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS saved_workflows (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
                    name VARCHAR(120) NOT NULL,
                    definition JSONB NOT NULL,
                    digest CHAR(64) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS saved_workflows_user_updated_idx ON saved_workflows (user_id, updated_at DESC)"
            )


database = Database()
