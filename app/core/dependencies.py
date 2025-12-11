"""Зависимости FastAPI для аутентификации."""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> "User":
    """Получить текущего пользователя из токена.

    Args:
        token: JWT токен
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

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: Optional[str] = payload.get("sub")
    token_type: Optional[str] = payload.get("type")

    if user_id_str is None or token_type != "access":
        raise credentials_exception

    repo = UserRepository(db)
    user = repo.get_by_id(int(user_id_str))
    if user is None:
        raise credentials_exception

    return user

