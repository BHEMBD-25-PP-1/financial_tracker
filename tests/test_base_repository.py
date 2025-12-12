"""Тесты для BaseRepository."""

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.db import session as db_session
from app.db.base import Base
from app.db.models import User
from app.repositories.base_repository import BaseRepository


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
    session = db_session.SessionLocal()
    repo = BaseRepository(User, session)
    yield repo
    session.close()


@pytest.fixture
def test_user():
    """Создание тестового пользователя."""
    from app.repositories.user_repository import UserRepository
    
    session = db_session.SessionLocal()
    try:
        existing_user = session.query(User).filter(User.login == "test_user").first()
        if existing_user:
            yield existing_user
        else:
            user_repo = UserRepository(db_session=session)
            user = user_repo.add(
                first_name="Test",
                last_name="User",
                login="test_user",
                password="testpassword123"
            )
            session.commit()
            session.refresh(user)
            yield user
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_get_success(repo, test_user):
    """Тест получения объекта по ID."""
    user = repo.get(test_user.id)
    
    assert user is not None
    assert user.id == test_user.id
    assert user.login == test_user.login


def test_get_not_found(repo):
    """Тест получения несуществующего объекта."""
    user = repo.get(99999)
    assert user is None


def test_get_all_success(repo, test_user):
    """Тест получения всех объектов."""
    users = repo.get_all()
    
    assert len(users) >= 1
    user_ids = [u.id for u in users]
    assert test_user.id in user_ids


def test_get_all_with_pagination(repo, test_user):
    """Тест получения объектов с пагинацией."""
    from app.repositories.user_repository import UserRepository
    session = db_session.SessionLocal()
    try:
        user_repo = UserRepository(db_session=session)
        user2 = user_repo.add(
            first_name="Test2",
            last_name="User2",
            login="test_user2",
            password="testpassword123"
        )
        session.commit()
        session.refresh(user2)
        
        users = repo.get_all(skip=0, limit=1)
        assert len(users) == 1
        
        users = repo.get_all(skip=1, limit=1)
        assert len(users) == 1
    finally:
        session.close()


def test_create_success(repo):
    """Тест создания объекта."""
    from app.core.security import get_password_hash
    
    new_user = User(
        first_name="New",
        last_name="User",
        login="new_user",
        password_hash=get_password_hash("password123")
    )
    
    created = repo.create(new_user)
    
    assert created.id is not None
    assert created.login == "new_user"
    
    session = db_session.SessionLocal()
    try:
        db_user = session.query(User).filter_by(id=created.id).first()
        assert db_user is not None
        assert db_user.login == "new_user"
    finally:
        session.close()


def test_update_success(repo, test_user):
    """Тест обновления объекта."""
    user = repo.get(test_user.id)
    user.first_name = "Updated"
    
    updated = repo.update(user)
    
    assert updated.first_name == "Updated"
    
    session = db_session.SessionLocal()
    try:
        db_user = session.query(User).filter_by(id=test_user.id).first()
        assert db_user.first_name == "Updated"
    finally:
        session.close()


def test_delete_success(repo, test_user):
    """Тест удаления объекта."""
    user = repo.get(test_user.id)
    user_id = user.id
    repo.delete(user)
    
    session = db_session.SessionLocal()
    try:
        db_user = session.query(User).filter_by(id=user_id).first()
        assert db_user is None
    finally:
        session.close()
