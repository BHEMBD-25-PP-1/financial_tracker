"""Модели данных для Auth API.

Автоматически сгенерировано из openapi-specs/auth-service.yaml
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RegisterRequest(BaseModel):
    """Запрос на регистрацию пользователя."""

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    login: str = Field(
        ..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$"
    )
    password: str = Field(..., min_length=8, max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "ivan_user",
                "password": "securePassword123",
            }
        }
    )


class LoginRequest(BaseModel):
    """Запрос на авторизацию."""

    login: str = Field(...)
    password: str = Field(...)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "login": "ivan_user",
                "password": "securePassword123",
            }
        }
    )


class User(BaseModel):
    """Модель пользователя."""

    id: int
    first_name: str
    last_name: str
    login: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "first_name": "Иван",
                "last_name": "Иванов",
                "login": "ivan_user",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }
    )


class LoginResponse(BaseModel):
    """Ответ на авторизацию."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: User

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": 1,
                    "first_name": "Иван",
                    "last_name": "Иванов",
                    "login": "ivan_user",
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z",
                },
            }
        }
    )


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена."""

    refresh_token: str = Field(...)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }
    )


class TokenResponse(BaseModel):
    """Ответ с токенами."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class ChangePasswordRequest(BaseModel):
    """Запрос на смену пароля."""

    current_password: str = Field(...)
    new_password: str = Field(..., min_length=8, max_length=100)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "oldPassword123",
                "new_password": "newPassword123",
            }
        }
    )


class ChangePasswordResponse(BaseModel):
    """Ответ на смену пароля."""

    message: str = "Пароль успешно изменен"


class Error(BaseModel):
    """Модель ошибки."""

    detail: str
    error_code: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Описание ошибки",
                "error_code": "VALIDATION_ERROR",
            }
        }
    )
