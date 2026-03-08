import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

PHONE_PATTERN = re.compile(r"^\+?\d{9,15}$")


class RegisterRequest(BaseModel):
    phone: str = Field(min_length=9, max_length=15)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not PHONE_PATTERN.match(value):
            raise ValueError("Phone must contain only digits and optional leading +")
        return value


class LoginRequest(BaseModel):
    phone: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(from_attributes=True)
