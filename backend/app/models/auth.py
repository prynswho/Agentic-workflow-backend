"""Request and response models for local account authentication."""

from pydantic import BaseModel, Field, field_validator


class SignupRequest(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    security_string: str = Field(min_length=8, max_length=256)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email or email.startswith("@") or email.endswith("@"):
            raise ValueError("A valid email address is required.")
        return email

    @field_validator("username")
    @classmethod
    def normalise_username(cls, value: str) -> str:
        return value.strip()


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalise_email(cls, value: str) -> str:
        return value.strip().lower()


class PasswordResetRequest(SignupRequest):
    """Uses the stored recovery/security string to authorize a new password."""
