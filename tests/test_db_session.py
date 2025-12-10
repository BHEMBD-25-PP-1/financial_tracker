import importlib
import os
from unittest.mock import MagicMock

import pytest


def _reload_session(monkeypatch, *, create_engine_mock=None, session_factory=None):
    """Reload app.db.session with patched sqlalchemy.create_engine/sessionmaker."""
    module_name = "app.db.session"
    importlib.sys.modules.pop(module_name, None)
    with monkeypatch.context() as m:
        if create_engine_mock:
            m.setattr("sqlalchemy.create_engine", create_engine_mock)
        if session_factory:
            m.setattr("sqlalchemy.orm.sessionmaker", session_factory)
        # Ensure DATABASE_URL is present to avoid fallback surprises
        m.setenv("DATABASE_URL", os.getenv("DATABASE_URL", "postgresql://test"))
        session_module = importlib.import_module(module_name)
    return session_module


def test_create_engine_called_with_params(monkeypatch):
    engine_mock = MagicMock(name="engine")
    create_engine_mock = MagicMock(return_value=engine_mock)

    session_module = _reload_session(monkeypatch, create_engine_mock=create_engine_mock)

    create_engine_mock.assert_called_once()
    args, kwargs = create_engine_mock.call_args
    assert args[0] == session_module.DATABASE_URL
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 20
    assert kwargs["pool_pre_ping"] is True
    assert kwargs["pool_recycle"] == 3600
    assert kwargs["echo"] is False
    # Engine returned by factory is used in SessionLocal binding
    assert session_module.engine is engine_mock


def test_get_db_yields_and_closes(monkeypatch):
    session_instance = MagicMock(name="session")

    def fake_sessionmaker(bind=None, autocommit=None, autoflush=None):
        return MagicMock(return_value=session_instance)

    session_module = _reload_session(monkeypatch, session_factory=fake_sessionmaker)

    gen = session_module.get_db()
    db = next(gen)
    assert db is session_instance

    # Closing generator should trigger finally and close session
    gen.close()
    session_instance.close.assert_called_once()

