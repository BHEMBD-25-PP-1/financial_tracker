"""Тесты для core/security.py."""

import sys
from pathlib import Path
from datetime import timedelta
from unittest.mock import patch

import pytest

# Ensure project modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_get_password_hash_success():
    """Тест успешного хеширования пароля."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert hashed is not None
    assert hashed != password
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_get_password_hash_empty_password():
    """Тест хеширования пустого пароля."""
    with pytest.raises(ValueError, match="Password cannot be empty"):
        get_password_hash("")


def test_get_password_hash_none_password():
    """Тест хеширования None пароля."""
    with pytest.raises(ValueError, match="Password cannot be empty"):
        get_password_hash(None)


def test_get_password_hash_long_password():
    """Тест хеширования очень длинного пароля (более 72 байт)."""
    long_password = "A" * 100
    hashed = get_password_hash(long_password)
    
    assert hashed is not None
    assert len(hashed) > 0


def test_verify_password_success():
    """Тест успешной проверки пароля."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed) is True


def test_verify_password_wrong_password():
    """Тест проверки неверного пароля."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password("wrongpassword", hashed) is False


def test_verify_password_empty_plain():
    """Тест проверки с пустым паролем."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password("", hashed) is False


def test_verify_password_empty_hashed():
    """Тест проверки с пустым хешем."""
    assert verify_password("password", "") is False


def test_verify_password_none_plain():
    """Тест проверки с None паролем."""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(None, hashed) is False


def test_verify_password_none_hashed():
    """Тест проверки с None хешем."""
    assert verify_password("password", None) is False


def test_create_access_token_success():
    """Тест успешного создания access токена."""
    data = {"sub": "1"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_custom_expires():
    """Тест создания access токена с кастомным временем жизни."""
    data = {"sub": "1"}
    expires_delta = timedelta(minutes=60)
    token = create_access_token(data, expires_delta=expires_delta)
    
    assert token is not None
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("type") == "access"
    assert payload.get("sub") == "1"


def test_create_access_token_contains_type():
    """Тест что access токен содержит тип."""
    data = {"sub": "1"}
    token = create_access_token(data)
    payload = decode_token(token)
    
    assert payload is not None
    assert payload.get("type") == "access"


def test_create_refresh_token_success():
    """Тест успешного создания refresh токена."""
    data = {"sub": "1"}
    token = create_refresh_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token_contains_type():
    """Тест что refresh токен содержит тип."""
    data = {"sub": "1"}
    token = create_refresh_token(data)
    payload = decode_token(token)
    
    assert payload is not None
    assert payload.get("type") == "refresh"


def test_decode_token_success():
    """Тест успешного декодирования токена."""
    data = {"sub": "1", "type": "access"}
    token = create_access_token(data)
    
    payload = decode_token(token)
    
    assert payload is not None
    assert payload.get("sub") == "1"
    assert payload.get("type") == "access"


def test_decode_token_invalid():
    """Тест декодирования невалидного токена."""
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)
    
    assert payload is None


def test_decode_token_empty():
    """Тест декодирования пустого токена."""
    payload = decode_token("")
    assert payload is None


def test_decode_token_malformed():
    """Тест декодирования неправильно сформированного токена."""
    payload = decode_token("not.a.valid.jwt.token")
    assert payload is None


def test_decode_token_wrong_secret():
    """Тест декодирования токена с неправильным секретом."""
    with patch('app.core.security.SECRET_KEY', 'secret1'):
        data = {"sub": "1"}
        token = create_access_token(data)
    
    # Пытаемся декодировать с другим секретом
    with patch('app.core.security.SECRET_KEY', 'secret2'):
        payload = decode_token(token)
        assert payload is None


def test_token_round_trip():
    """Тест полного цикла: создание и декодирование токена."""
    original_data = {"sub": "123", "custom": "value"}
    token = create_access_token(original_data)
    payload = decode_token(token)
    
    assert payload is not None
    assert payload.get("sub") == "123"
    assert payload.get("type") == "access"
    assert "exp" in payload


def test_access_and_refresh_tokens_different():
    """Тест что access и refresh токены разные."""
    data = {"sub": "1"}
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    assert access_token != refresh_token
    
    access_payload = decode_token(access_token)
    refresh_payload = decode_token(refresh_token)
    
    assert access_payload.get("type") == "access"
    assert refresh_payload.get("type") == "refresh"
