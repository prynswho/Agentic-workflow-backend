"""User persistence queries. All values are parameterised."""

from dataclasses import dataclass
from uuid import uuid4

from psycopg.errors import UniqueViolation

from app.db.database import database


@dataclass(frozen=True)
class User:
    id: str
    username: str
    email: str
    password_hash: str
    security_string_hash: str


class EmailAlreadyExistsError(ValueError):
    """Raised when the database's unique email constraint is violated."""


def _to_user(row: dict | None) -> User | None:
    if row is None:
        return None
    return User(
        id=str(row["id"]),
        username=row["username"] or row["email"].split("@", 1)[0],
        email=row["email"],
        password_hash=row["password_hash"],
        security_string_hash=row["security_string_hash"],
    )


def get_user_by_email(email: str) -> User | None:
    with database.connection() as connection:
        row = connection.execute(
            "SELECT id, username, email, password_hash, security_string_hash FROM app_users WHERE email = %s",
            (email.lower(),),
        ).fetchone()
    return _to_user(row)


def create_user(*, username: str, email: str, password_hash: str, security_string_hash: str) -> User:
    user_id = uuid4()
    try:
        with database.connection() as connection:
            connection.execute(
                """
                INSERT INTO app_users (id, username, email, password_hash, security_string_hash)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, username, email.lower(), password_hash, security_string_hash),
            )
    except UniqueViolation as exc:
        raise EmailAlreadyExistsError from exc
    return User(
        id=str(user_id),
        username=username,
        email=email.lower(),
        password_hash=password_hash,
        security_string_hash=security_string_hash,
    )


def update_password(*, user_id: str, password_hash: str) -> None:
    with database.connection() as connection:
        connection.execute(
            """
            UPDATE app_users
            SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (password_hash, user_id),
        )
