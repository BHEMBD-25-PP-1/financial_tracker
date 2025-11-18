import sys
from pathlib import Path

import pytest

# Ensure project modules are importable when running pytest from repo root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from db import SessionLocal, engine
from entity import Base, User
from user_repository import UserRepository


@pytest.fixture(scope="module", autouse=True)
def ensure_tables():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def clean_users_table():
    session = SessionLocal()
    session.query(User).delete()
    session.commit()
    session.close()
    yield
    session = SessionLocal()
    session.query(User).delete()
    session.commit()
    session.close()


@pytest.fixture
def repo():
    repository = UserRepository()
    yield repository
    repository.db.close()


def test_add_user_persists_record(repo):
    user = repo.add(name="Alice", email="alice@example.com")

    assert user.id is not None
    assert user.name == "Alice"
    assert user.email == "alice@example.com"

    session = SessionLocal()
    try:
        db_user = session.query(User).filter_by(id=user.id).one()
        assert db_user.name == "Alice"
        assert db_user.email == "alice@example.com"
    finally:
        session.close()


def test_get_by_id_returns_existing_user(repo):
    created = repo.add(name="Bob", email="bob@example.com")

    fetched = repo.get_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.name == "Bob"
    assert fetched.email == "bob@example.com"


def test_get_all_returns_all_users(repo):
    repo.add(name="Carol", email="carol@example.com")
    repo.add(name="Dave", email="dave@example.com")

    users = repo.get_all()

    assert len(users) == 2
    emails = sorted(user.email for user in users)
    assert emails == ["carol@example.com", "dave@example.com"]

