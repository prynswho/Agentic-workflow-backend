"""Account creation, authentication, and recovery use cases."""

from app.core.security import create_access_token, hash_secret, verify_secret
from app.db import DatabaseUnavailable
from app.db import users


class DuplicateEmailError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


def signup(*, username: str, email: str, password: str, security_string: str) -> dict:
    if users.get_user_by_email(email):
        raise DuplicateEmailError("An account already exists for this email address.")
    try:
        user = users.create_user(
            username=username,
            email=email,
            password_hash=hash_secret(password),
            security_string_hash=hash_secret(security_string),
        )
    except users.EmailAlreadyExistsError as exc:
        raise DuplicateEmailError("An account already exists for this email address.") from exc
    return {"id": user.id, "username": user.username, "email": user.email}


def login(*, email: str, password: str) -> dict:
    user = users.get_user_by_email(email)
    if user is None or not verify_secret(password, user.password_hash):
        # Keep the same error whether the account or password is wrong.
        raise InvalidCredentialsError("Invalid email or password.")
    token, expires_in = create_access_token(user_id=user.id, email=user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": expires_in,
        "user": {"id": user.id, "username": user.username, "email": user.email},
    }


def reset_password(*, email: str, security_string: str, password: str) -> None:
    user = users.get_user_by_email(email)
    if user is None or not verify_secret(security_string, user.security_string_hash):
        raise InvalidCredentialsError("Invalid email or security string.")
    users.update_password(user_id=user.id, password_hash=hash_secret(password))
