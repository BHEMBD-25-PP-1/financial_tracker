"""Зависимости FastAPI для аутентификации."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

# Используем HTTPBearer для простой Bearer авторизации в Swagger UI
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> "User":
    """Получить текущего пользователя из токена.

    Args:
        credentials: Bearer токен из заголовка Authorization
        db: Сессия базы данных

    Returns:
        User: Текущий пользователь

    Raises:
        HTTPException: Если токен невалидный или пользователь не найден
    """
    from app.db.models import User

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials.strip() if credentials.credentials else None
    if not token:
        raise credentials_exception

    payload = decode_token(token)
    if payload is None:
        # Пытаемся определить причину ошибки для более информативного сообщения
        from jose import jwt as jose_jwt
        try:
            # Пытаемся декодировать без проверки подписи, чтобы проверить срок действия
            jose_jwt.decode(token, options={"verify_signature": False, "verify_exp": True})
            # Если дошли сюда, значит проблема в подписи
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный токен (неверная подпись). Возможно, токен был создан с другим SECRET_KEY. Получите новый токен через /auth/login",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jose_jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен истек. Используйте /auth/refresh для получения нового токена",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Невалидный токен. Получите новый токен через /auth/login",
                headers={"WWW-Authenticate": "Bearer"},
            )

    user_id_str: Optional[str] = payload.get("sub")
    token_type: Optional[str] = payload.get("type")

    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен не содержит user_id",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Неверный тип токена: {token_type}. Ожидается 'access'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный формат user_id в токене",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise credentials_exception

    return user

