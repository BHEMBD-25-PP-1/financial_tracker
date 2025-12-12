"""Тесты для core/dependencies.py."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

# Ensure project modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.dependencies import get_current_user
from app.db.models import User

# Настройка для async тестов
pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_credentials():
    """Мок credentials."""
    credentials = MagicMock(unsafe_spec=HTTPAuthorizationCredentials)
    return credentials


@pytest.fixture
def mock_db():
    """Мок сессии БД."""
    return MagicMock()


@patch('app.core.dependencies.decode_token')
@patch('app.core.dependencies.UserRepository')
@patch('app.core.dependencies.get_db')
async def test_get_current_user_success(mock_get_db, mock_repo_class, mock_decode_token, mock_credentials, mock_db):
    """Тест успешного получения текущего пользователя."""
    mock_get_db.return_value = mock_db
    
    mock_payload = {
        "sub": "1",
        "type": "access",
        "exp": None
    }
    mock_decode_token.return_value = mock_payload
    
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    
    mock_user = MagicMock(unsafe_spec=User)
    mock_user.id = 1
    mock_repo.get_by_id.return_value = mock_user
    
    mock_credentials.credentials = "valid_token"
    
    result = await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert result.id == 1
    mock_decode_token.assert_called_once_with("valid_token")
    mock_repo.get_by_id.assert_called_once_with(1)


@patch('app.core.dependencies.get_db')
async def test_get_current_user_empty_token(mock_get_db, mock_credentials, mock_db):
    """Тест получения пользователя с пустым токеном."""
    mock_get_db.return_value = mock_db
    mock_credentials.credentials = ""
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@patch('app.core.dependencies.get_db')
async def test_get_current_user_none_token(mock_get_db, mock_credentials, mock_db):
    """Тест получения пользователя с None токеном."""
    mock_get_db.return_value = mock_db
    mock_credentials.credentials = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@patch('app.core.dependencies.decode_token')
@patch('app.core.dependencies.get_db')
async def test_get_current_user_invalid_token(mock_get_db, mock_decode_token, mock_credentials, mock_db):
    """Тест получения пользователя с невалидным токеном."""
    mock_get_db.return_value = mock_db
    mock_decode_token.return_value = None
    mock_credentials.credentials = "invalid_token"
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Невалидный токен" in exc_info.value.detail


@patch('app.core.dependencies.decode_token')
@patch('app.core.dependencies.get_db')
async def test_get_current_user_missing_sub(mock_get_db, mock_decode_token, mock_credentials, mock_db):
    """Тест получения пользователя с токеном без sub."""
    mock_get_db.return_value = mock_db
    mock_decode_token.return_value = {"type": "access"}
    mock_credentials.credentials = "token"
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "user_id" in exc_info.value.detail


@patch('app.core.dependencies.decode_token')
@patch('app.core.dependencies.get_db')
async def test_get_current_user_wrong_token_type(mock_get_db, mock_decode_token, mock_credentials, mock_db):
    """Тест получения пользователя с refresh токеном вместо access."""
    mock_get_db.return_value = mock_db
    mock_decode_token.return_value = {"sub": "1", "type": "refresh"}
    mock_credentials.credentials = "refresh_token"
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Неверный тип токена" in exc_info.value.detail


@patch('app.core.dependencies.decode_token')
@patch('app.core.dependencies.get_db')
async def test_get_current_user_invalid_user_id_format(mock_get_db, mock_decode_token, mock_credentials, mock_db):
    """Тест получения пользователя с невалидным форматом user_id."""
    mock_get_db.return_value = mock_db
    mock_decode_token.return_value = {"sub": "not_a_number", "type": "access"}
    mock_credentials.credentials = "token"
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Невалидный формат user_id" in exc_info.value.detail


@patch('app.core.dependencies.decode_token')
@patch('app.core.dependencies.UserRepository')
@patch('app.core.dependencies.get_db')
async def test_get_current_user_not_found(mock_get_db, mock_repo_class, mock_decode_token, mock_credentials, mock_db):
    """Тест получения пользователя, который не найден в БД."""
    mock_get_db.return_value = mock_db
    mock_decode_token.return_value = {"sub": "99999", "type": "access"}
    mock_credentials.credentials = "token"
    
    mock_repo = MagicMock()
    mock_repo_class.return_value = mock_repo
    mock_repo.get_by_id.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Не удалось проверить учетные данные" in exc_info.value.detail


@patch('app.core.dependencies.decode_token')
@patch('app.core.dependencies.get_db')
async def test_get_current_user_whitespace_token(mock_get_db, mock_decode_token, mock_credentials, mock_db):
    """Тест получения пользователя с токеном из пробелов."""
    mock_get_db.return_value = mock_db
    mock_credentials.credentials = "   "
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=mock_credentials, db=mock_db)
    
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
