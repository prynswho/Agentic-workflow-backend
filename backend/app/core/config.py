"""Runtime configuration for the reorganised FastAPI application."""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Settings read once when the API process starts.

    ``database_url`` is preferred. The individual ``POSTGRES_*`` values make
    local Docker/Postgres setups convenient without putting a URL in source.
    """

    max_parallel_nodes: int = int(os.getenv("MAX_PARALLEL_NODES", "4"))
    database_url: str = os.getenv("DATABASE_URL", "")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "agentic_workflow")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    access_token_ttl_minutes: int = int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "1440"))
    bcrypt_rounds: int = int(os.getenv("BCRYPT_ROUNDS", "12"))

    @property
    def resolved_database_url(self) -> str:
        """Return the configured PostgreSQL URL, or build one from PG vars."""
        if self.database_url:
            return self.database_url
        if not self.postgres_password:
            return ""
        # psycopg accepts a standard PostgreSQL connection URI.
        from urllib.parse import quote

        return (
            "postgresql://"
            f"{quote(self.postgres_user, safe='')}:{quote(self.postgres_password, safe='')}"
            f"@{self.postgres_host}:{self.postgres_port}/{quote(self.postgres_db, safe='')}"
        )


settings = Settings()
