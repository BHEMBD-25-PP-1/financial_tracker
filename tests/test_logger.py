import logging
from logging import Logger, LogRecord

from app.core.logger import UserIdFilter, setup_logging


def _make_loggers():
    """Utility to provide isolated logger instances for tests."""
    root_logger = Logger("root")
    sa_logger = Logger("sqlalchemy.engine")
    return root_logger, sa_logger


def test_user_id_filter_adds_prefix():
    user_filter = UserIdFilter()
    record = LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="message",
        args=(),
        exc_info=None,
    )
    record.user_id = 42

    result = user_filter.filter(record)

    assert result is True
    assert record.msg == "[user:42] message"


def test_user_id_filter_does_not_duplicate_prefix():
    user_filter = UserIdFilter()
    record = LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="[user:42] message",
        args=(),
        exc_info=None,
    )
    record.user_id = 42

    result = user_filter.filter(record)

    assert result is True
    assert record.msg == "[user:42] message"


def test_setup_logging_creates_handlers(monkeypatch, tmp_path):
    root_logger, sa_logger = _make_loggers()

    def fake_get_logger(name=None):
        if name in (None, ""):
            return root_logger
        if name == "sqlalchemy.engine":
            return sa_logger
        return Logger(name)

    monkeypatch.setattr(logging, "getLogger", fake_get_logger)

    logger = setup_logging(log_dir=tmp_path)

    try:
        assert logger is root_logger
        assert logger.level == logging.INFO
        # Two handlers: rotating file + stream
        assert len(logger.handlers) == 2
        for handler in logger.handlers:
            # UserIdFilter should be attached
            assert any(isinstance(f, UserIdFilter) for f in handler.filters)
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)


def test_setup_logging_does_not_duplicate_handlers(monkeypatch, tmp_path):
    root_logger, sa_logger = _make_loggers()
    existing_handler = logging.StreamHandler()
    root_logger.addHandler(existing_handler)

    def fake_get_logger(name=None):
        if name in (None, ""):
            return root_logger
        if name == "sqlalchemy.engine":
            return sa_logger
        return Logger(name)

    monkeypatch.setattr(logging, "getLogger", fake_get_logger)

    logger = setup_logging(log_dir=tmp_path)

    try:
        # Handlers should remain as they were because logger already had one
        assert logger.handlers == [existing_handler]
    finally:
        for handler in list(logger.handlers):
            handler.close()
            logger.removeHandler(handler)

