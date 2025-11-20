"""Пакет для тестирования интеграции с PostgreSQL."""

from python_postgres_test.config import DATABASE_URL
from python_postgres_test.entity import Base, User
from python_postgres_test.db import engine, SessionLocal
from python_postgres_test.user_repository import UserRepository

__all__ = [
    "DATABASE_URL",
    "Base",
    "User",
    "engine",
    "SessionLocal",
    "UserRepository",
]

