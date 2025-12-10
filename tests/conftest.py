import logging
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.repositories.user_repository import UserRepository
from app.db import session as db_session


@pytest.fixture
def db_session_mock() -> MagicMock:
    """Mocked SQLAlchemy Session with common methods stubbed."""
    mock = MagicMock(spec=Session)
    # Ensure commit/rollback/close/flush/refresh exist for context manager paths
    for method in ("commit", "rollback", "close", "flush", "refresh"):
        getattr(mock, method).return_value = None
    # query returns MagicMock to allow chaining in tests
    mock.query.return_value = MagicMock()
    return mock


@pytest.fixture
def patch_session_local(monkeypatch, db_session_mock: MagicMock):
    """Patch SessionLocal to return mocked session."""
    monkeypatch.setattr(db_session, "SessionLocal", MagicMock(return_value=db_session_mock))
    return db_session_mock


@pytest.fixture
def mock_engine(monkeypatch):
    """Patch create_engine to avoid real DB connections."""
    engine_mock = MagicMock(name="engine")
    monkeypatch.setattr(db_session, "create_engine", MagicMock(return_value=engine_mock))
    return engine_mock


@pytest.fixture
def user_repo(db_session_mock: MagicMock) -> UserRepository:
    """UserRepository bound to mocked session."""
    return UserRepository(db_session=db_session_mock)


@pytest.fixture
def logger_mock(monkeypatch) -> MagicMock:
    """Patch logging.getLogger to return a mock logger."""
    logger = MagicMock(spec=logging.Logger)
    monkeypatch.setattr(logging, "getLogger", MagicMock(return_value=logger))
    return logger

