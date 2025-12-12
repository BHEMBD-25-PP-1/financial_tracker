"""Утилиты для безопасности: JWT токены и хеширование паролей."""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Загружаем .env если ещё не загружен
from app.core.config import DATABASE_URL  # noqa: F401 - триггерит загрузку .env

# Настройки JWT
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверить пароль.

    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хешированный пароль

    Returns:
        bool: True если пароль верный
    """
    if not plain_password or not hashed_password:
        return False
    # Убеждаемся, что пароль - это строка и не превышает 72 байта
    if isinstance(plain_password, bytes):
        plain_password = plain_password.decode('utf-8')
    # Обрезаем пароль до 72 байт для совместимости с bcrypt
    plain_password_bytes = plain_password.encode('utf-8')
    if len(plain_password_bytes) > 72:
        plain_password = plain_password_bytes[:72].decode('utf-8', errors='ignore')
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Получить хеш пароля.

    Args:
        password: Пароль в открытом виде

    Returns:
        str: Хешированный пароль
    """
    if not password:
        raise ValueError("Password cannot be empty")
    # Убеждаемся, что пароль - это строка
    if isinstance(password, bytes):
        password = password.decode('utf-8')
    # Обрезаем пароль до 72 байт для совместимости с bcrypt
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password = password_bytes[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создать access токен.

    Args:
        data: Данные для включения в токен
        expires_delta: Время жизни токена

    Returns:
        str: JWT токен
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Создать refresh токен.

    Args:
        data: Данные для включения в токен

    Returns:
        str: JWT refresh токен
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """Декодировать токен.

    Args:
        token: JWT токен

    Returns:
        dict: Данные из токена или None если токен невалидный
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

