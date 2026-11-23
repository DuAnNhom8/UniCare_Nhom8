"""Input/Output xác thực, không bao giờ trả password_hash."""
import re
from pydantic import BaseModel, Field, field_validator


class RegisterRequest(BaseModel):
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    role: str = 'CANDIDATE'

    @field_validator('email')
    @classmethod
    def email_format(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Email không hợp lệ')
        return value

    @field_validator('role')
    @classmethod
    def only_public_roles(cls, value: str) -> str:
        value = value.upper()
        if value not in ('CANDIDATE', 'EMPLOYER'):
            raise ValueError('Chỉ được đăng ký CANDIDATE hoặc EMPLOYER')
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in: int = 7200


class CurrentUser(BaseModel):
    user_id: int
    email: str
    role: str
    model_config = {'from_attributes': True}
