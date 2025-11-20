"""Тесты для UserRepository."""

import sys
from pathlib import Path

import pytest

# Ensure project modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from python_postgres_test.db import SessionLocal, engine
from python_postgres_test.entity import Base, User
from python_postgres_test.logger import setup_logging
from python_postgres_test.user_repository import UserRepository


# Настройка логирования для тестов
setup_logging()


def _clean_users_table():
    """Вспомогательная функция для очистки таблицы пользователей."""
    session = SessionLocal()
    try:
        session.query(User).delete()
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope="module", autouse=True)
def ensure_tables():
    """Создание таблиц перед всеми тестами."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def clean_users_table():
    """Очистка таблицы пользователей перед и после каждого теста."""
    _clean_users_table()
    yield
    _clean_users_table()


@pytest.fixture
def repo():
    """Фикстура для создания репозитория."""
    with UserRepository() as repository:
        yield repository


def test_add_user_persists_record(repo):
    """Тест создания пользователя и сохранения в БД."""
    user = repo.add(name="Alice", email="alice@example.com")

    assert user.id is not None
    assert user.name == "Alice"
    assert user.email == "alice@example.com"

    # Проверяем, что пользователь действительно сохранен в БД
    session = SessionLocal()
    try:
        db_user = session.query(User).filter_by(id=user.id).one()
        assert db_user.name == "Alice"
        assert db_user.email == "alice@example.com"
    finally:
        session.close()


def test_get_by_id_returns_existing_user(repo):
    """Тест получения пользователя по ID."""
    created = repo.add(name="Bob", email="bob@example.com")

    fetched = repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Bob"
    assert fetched.email == "bob@example.com"


def test_get_all_returns_all_users(repo):
    """Тест получения всех пользователей."""
    repo.add(name="Carol", email="carol@example.com")
    repo.add(name="Dave", email="dave@example.com")

    users = repo.get_all()

    assert len(users) == 2
    emails = sorted(user.email for user in users)
    assert emails == ["carol@example.com", "dave@example.com"]


def test_add_duplicate_email_raises_error(repo):
    """Тест создания пользователя с дублирующимся email."""
    repo.add(name="Alice", email="alice@example.com")
    
    # Попытка создать пользователя с таким же email должна вызвать ValueError
    with pytest.raises(ValueError, match="already exists"):
        repo.add(name="Bob", email="alice@example.com")


def test_get_by_id_returns_none_for_nonexistent_user(repo):
    """Тест получения несуществующего пользователя."""
    user = repo.get_by_id(99999)
    
    assert user is None


def test_get_all_returns_empty_list(repo):
    """Тест получения пустого списка пользователей."""
    users = repo.get_all()
    
    assert users == []
    assert len(users) == 0


def test_add_user_with_invalid_email_raises_error(repo):
    """Тест валидации email при создании пользователя."""
    # Невалидный email
    with pytest.raises(ValueError, match="Invalid email format"):
        repo.add(name="Alice", email="invalid-email")
    
    # Пустой email
    with pytest.raises(ValueError, match="Email cannot be empty"):
        repo.add(name="Alice", email="")


def test_add_user_with_invalid_name_raises_error(repo):
    """Тест валидации имени при создании пользователя."""
    # Пустое имя
    with pytest.raises(ValueError, match="Name cannot be empty"):
        repo.add(name="", email="alice@example.com")
    
    # Имя только из пробелов
    with pytest.raises(ValueError, match="Name cannot be empty"):
        repo.add(name="   ", email="alice@example.com")
    
    # Имя слишком длинное
    with pytest.raises(ValueError, match="Name too long"):
        repo.add(name="A" * 101, email="alice@example.com")
