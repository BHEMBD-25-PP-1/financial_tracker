"""Тесты для UserRepository."""

import sys
from pathlib import Path

import pytest

# Ensure project modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.db import session as db_session
from app.db.base import Base
from app.db.models import User
from app.repositories.user_repository import UserRepository


@pytest.fixture(autouse=True)
def clean_users_table():
    """Очистка таблицы пользователей перед и после каждого теста."""
    session = db_session.SessionLocal()
    try:
        session.query(User).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
    yield
    session = db_session.SessionLocal()
    try:
        session.query(User).delete()
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def repo():
    """Фикстура для создания репозитория."""
    with UserRepository() as repository:
        yield repository


def test_add_user_persists_record(repo):
    """Тест создания пользователя и сохранения в БД."""
    user = repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")

    assert user.id is not None
    assert user.first_name == "Alice"
    assert user.last_name == "Smith"
    assert user.login == "alice"

    session = db_session.SessionLocal()
    try:
        db_user = session.query(User).filter_by(id=user.id).one()
        assert db_user.first_name == "Alice"
        assert db_user.last_name == "Smith"
        assert db_user.login == "alice"
    finally:
        session.close()


def test_get_by_id_returns_existing_user(repo):
    """Тест получения пользователя по ID."""
    created = repo.add(first_name="Bob", last_name="Jones", login="bob", password="password123")

    fetched = repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.first_name == "Bob"
    assert fetched.last_name == "Jones"
    assert fetched.login == "bob"


def test_get_all_returns_all_users(repo):
    """Тест получения всех пользователей."""
    repo.add(first_name="Carol", last_name="White", login="carol", password="password123")
    repo.add(first_name="Dave", last_name="Black", login="dave", password="password123")

    users = repo.get_all()

    assert len(users) == 2
    logins = sorted(user.login for user in users)
    assert logins == ["carol", "dave"]


def test_add_duplicate_login_raises_error(repo):
    """Тест создания пользователя с дублирующимся login."""
    repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    with pytest.raises(ValueError, match="already exists"):
        repo.add(first_name="Bob", last_name="Jones", login="alice", password="password123")


def test_get_by_id_returns_none_for_nonexistent_user(repo):
    """Тест получения несуществующего пользователя."""
    user = repo.get_by_id(99999)
    
    assert user is None


def test_get_all_returns_empty_list(repo):
    """Тест получения пустого списка пользователей."""
    users = repo.get_all()
    
    assert users == []
    assert len(users) == 0


def test_add_user_with_invalid_login_raises_error(repo):
    """Тест валидации login при создании пользователя."""
    with pytest.raises(ValueError, match="Login cannot be empty"):
        repo.add(first_name="Alice", last_name="Smith", login="", password="password123")
    
    with pytest.raises(ValueError, match="Login too short"):
        repo.add(first_name="Alice", last_name="Smith", login="ab", password="password123")
    
    with pytest.raises(ValueError, match="can only contain letters"):
        repo.add(first_name="Alice", last_name="Smith", login="alice-smith", password="password123")


def test_add_user_with_invalid_name_raises_error(repo):
    """Тест валидации имени при создании пользователя."""
    with pytest.raises(ValueError, match="cannot be empty"):
        repo.add(first_name="", last_name="Smith", login="alice", password="password123")
    
    with pytest.raises(ValueError, match="cannot be empty"):
        repo.add(first_name="   ", last_name="Smith", login="alice", password="password123")
    
    with pytest.raises(ValueError, match="too long"):
        repo.add(first_name="A" * 101, last_name="Smith", login="alice", password="password123")


def test_get_by_login_success(repo):
    """Тест получения пользователя по логину."""
    created = repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    fetched = repo.get_by_login("alice")
    
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.login == "alice"


def test_get_by_login_case_insensitive(repo):
    """Тест получения пользователя по логину (регистронезависимо)."""
    created = repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    fetched = repo.get_by_login("ALICE")
    
    assert fetched is not None
    assert fetched.id == created.id


def test_get_by_login_not_found(repo):
    """Тест получения несуществующего пользователя по логину."""
    user = repo.get_by_login("nonexistent")
    assert user is None


def test_get_by_login_with_whitespace(repo):
    """Тест получения пользователя по логину с пробелами."""
    created = repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    fetched = repo.get_by_login("  alice  ")
    
    assert fetched is not None
    assert fetched.id == created.id


def test_verify_user_success(repo):
    """Тест успешной верификации пользователя."""
    repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    user = repo.verify_user("alice", "password123")
    
    assert user is not None
    assert user.login == "alice"


def test_verify_user_wrong_password(repo):
    """Тест верификации с неверным паролем."""
    repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    user = repo.verify_user("alice", "wrongpassword")
    
    assert user is None


def test_verify_user_not_found(repo):
    """Тест верификации несуществующего пользователя."""
    user = repo.verify_user("nonexistent", "password123")
    
    assert user is None


def test_update_password_success(repo):
    """Тест успешного обновления пароля."""
    created = repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    result = repo.update_password(created.id, "newpassword123")
    
    assert result is True
    
    user = repo.verify_user("alice", "newpassword123")
    assert user is not None
    
    user = repo.verify_user("alice", "password123")
    assert user is None


def test_update_password_user_not_found(repo):
    """Тест обновления пароля несуществующего пользователя."""
    result = repo.update_password(99999, "newpassword123")
    
    assert result is False


def test_update_password_short_password(repo):
    """Тест обновления пароля с коротким паролем."""
    created = repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        repo.update_password(created.id, "short")


def test_update_password_empty_password(repo):
    """Тест обновления пароля с пустым паролем."""
    created = repo.add(first_name="Alice", last_name="Smith", login="alice", password="password123")
    
    with pytest.raises(ValueError, match="Password must be at least 8 characters"):
        repo.update_password(created.id, "")

