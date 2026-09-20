"""Public authentication endpoints backed by PostgreSQL."""

from fastapi import APIRouter, HTTPException, status

from app.core.security import SecurityConfigurationError
from app.db import DatabaseUnavailable
from app.models.auth import LoginRequest, PasswordResetRequest, SignupRequest
from app.services.auth import DuplicateEmailError, InvalidCredentialsError, login, reset_password, signup

router = APIRouter(prefix="/auth", tags=["auth"])


def _database_http_error(exc: DatabaseUnavailable) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup_user(request: SignupRequest) -> dict:
    try:
        user = signup(
            username=request.username,
            email=request.email,
            password=request.password,
            security_string=request.security_string,
        )
    except DatabaseUnavailable as exc:
        raise _database_http_error(exc) from exc
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return {"status": "success", "user": user}


@router.post("/login")
def login_user(request: LoginRequest) -> dict:
    try:
        return {"status": "success", **login(email=request.email, password=request.password)}
    except DatabaseUnavailable as exc:
        raise _database_http_error(exc) from exc
    except SecurityConfigurationError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/reset-password")
def reset_user_password(request: PasswordResetRequest) -> dict:
    try:
        reset_password(
            email=request.email,
            security_string=request.security_string,
            password=request.password,
        )
    except DatabaseUnavailable as exc:
        raise _database_http_error(exc) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return {"status": "success", "message": "Password updated successfully."}
