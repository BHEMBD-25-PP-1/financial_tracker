import logging
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.repositories.user_repository import UserRepository
from app.db import session as db_session
from app.db.base import Base


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


_test_db_engine = None


def _get_test_db_engine():
    """Создает или возвращает существующий тестовый engine."""
    global _test_db_engine
    if _test_db_engine is None:
        from sqlalchemy import String, Enum as SQLEnum
        
        _test_db_engine = create_engine("sqlite:///:memory:", echo=False)
        
        original_columns = {}
        for table in Base.metadata.tables.values():
            for column in table.columns:
                if isinstance(column.type, SQLEnum):
                    original_columns[(table.name, column.name)] = column.type
                    column.type = String(20)
        
        Base.metadata.create_all(bind=_test_db_engine)
        
        for (table_name, col_name), orig_type in original_columns.items():
            table = Base.metadata.tables[table_name]
            table.columns[col_name].type = orig_type
    
    return _test_db_engine


@pytest.fixture(scope="function", autouse=True)
def setup_test_db_for_repositories(monkeypatch, request):
    """Автоматически настраивает тестовую БД для тестов репозиториев."""
    test_file = str(request.node.fspath).replace('\\', '/')
    
    if any(x in test_file for x in ['test_transaction_repository', 'test_user_repository', 'test_group_repository', 'test_base_repository']):
        test_engine = _get_test_db_engine()
        TestSessionLocal = sessionmaker(bind=test_engine, autocommit=False, autoflush=False)
        
        # Заменяем SessionLocal во всех нужных местах
        monkeypatch.setattr(db_session, "SessionLocal", TestSessionLocal)
        monkeypatch.setattr(db_session, "engine", test_engine)
        
        # Также нужно обновить импорты в репозиториях
        from app.repositories import transaction_repository, user_repository, group_repository
        monkeypatch.setattr(transaction_repository, "SessionLocal", TestSessionLocal)
        monkeypatch.setattr(user_repository, "SessionLocal", TestSessionLocal)
        monkeypatch.setattr(group_repository, "SessionLocal", TestSessionLocal)

