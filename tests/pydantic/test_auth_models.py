import pytest
from pydantic import ValidationError

from app.auth import models as m


def test_register_request_valid():
    data = {
        "first_name": "Иван",
        "last_name": "Иванов",
        "login": "ivan_user",
        "password": "securePassword123",
    }
    obj = m.RegisterRequest(**data)
    assert obj.login == "ivan_user"


@pytest.mark.parametrize(
    "field,value",
    [
        ("login", "bad login"),  # пробелы нарушают pattern
        ("password", "short"),
    ],
)
def test_register_request_invalid(field, value):
    base = {
        "first_name": "A",
        "last_name": "B",
        "login": "ok_user",
        "password": "goodpassword",
    }
    base[field] = value
    with pytest.raises(ValidationError):
        m.RegisterRequest(**base)


def test_login_request_missing_password():
    with pytest.raises(ValidationError):
        m.LoginRequest(login="user")


def test_login_response_defaults_token_type():
    user = m.User(
        id=1, first_name="A", last_name="B", login="ab", created_at="2024-01-01T00:00:00Z", updated_at="2024-01-01T00:00:00Z"
    )
    obj = m.LoginResponse(access_token="a", refresh_token="b", user=user)
    assert obj.token_type == "bearer"


def test_token_response_defaults():
    obj = m.TokenResponse(access_token="a", refresh_token="b")
    assert obj.token_type == "bearer"


def test_change_password_request_invalid_min_length():
    with pytest.raises(ValidationError):
        m.ChangePasswordRequest(current_password="old", new_password="short")

