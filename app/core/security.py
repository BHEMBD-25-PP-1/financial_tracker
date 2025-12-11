"""Утилиты для безопасности: JWT токены и хеширование паролей."""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

# Настройки JWT
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Вынести в переменные окружения
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

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
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, AttributeError, TypeError):
        # Обход проблемы совместимости passlib с bcrypt 5.0.0
        import bcrypt
        password_bytes = plain_password.encode('utf-8')
        # Обрезаем пароль до 72 байт если нужно (ограничение bcrypt)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        hash_bytes = hashed_password.encode('utf-8')
        try:
            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception:
            return False


def get_password_hash(password: str) -> str:
    """Получить хеш пароля.

    Args:
        password: Пароль в открытом виде

    Returns:
        str: Хешированный пароль
    """
    # Обход проблемы совместимости passlib с bcrypt 5.0.0
    try:
        return pwd_context.hash(password)
    except (ValueError, AttributeError):
        # Если возникает ошибка, используем прямой вызов bcrypt
        import bcrypt
        password_bytes = password.encode('utf-8')
        # Обрезаем пароль до 72 байт если нужно (ограничение bcrypt)
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')


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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
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

