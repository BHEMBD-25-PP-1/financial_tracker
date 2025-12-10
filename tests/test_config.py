import importlib
import os
from urllib.parse import quote_plus

import pytest


def _reload_config(monkeypatch, env: dict):
    """Reload app.core.config with patched env vars."""
    # Clear module to force re-evaluation
    if "app.core.config" in list(importlib.sys.modules.keys()):
        importlib.sys.modules.pop("app.core.config")
    with monkeypatch.context() as m:
        for key in list(os.environ.keys()):
            if key.startswith("DB_") or key == "DATABASE_URL":
                m.delenv(key, raising=False)
        for k, v in env.items():
            m.setenv(k, v)
        config = importlib.import_module("app.core.config")
    return config


def test_default_database_url(monkeypatch):
    cfg = _reload_config(monkeypatch, {})
    assert cfg.DATABASE_URL.startswith("postgresql+psycopg2://postgres:@localhost:5432/financial_tracker")


def test_database_url_assembled_from_parts(monkeypatch):
    env = {
        "DB_USER": "user",
        "DB_PASSWORD": "p@ss word",
        "DB_HOST": "db.example",
        "DB_PORT": "6543",
        "DB_NAME": "ft",
    }
    cfg = _reload_config(monkeypatch, env)

    expected = (
        f"postgresql+psycopg2://{quote_plus(env['DB_USER'])}:"
        f"{quote_plus(env['DB_PASSWORD'])}@{env['DB_HOST']}:{env['DB_PORT']}/{env['DB_NAME']}"
    )
    assert cfg.DATABASE_URL == expected


def test_database_url_env_has_priority(monkeypatch):
    env = {
        "DATABASE_URL": "postgresql://custom-url",
        "DB_USER": "ignored",
        "DB_PASSWORD": "ignored",
    }
    cfg = _reload_config(monkeypatch, env)
    assert cfg.DATABASE_URL == env["DATABASE_URL"]

