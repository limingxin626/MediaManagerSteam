import os

import pytest
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker

from app.shared.database import create_sqlite_engine
from app.config import get_settings
from app.models import Base
from app.modules.repository import catalog as repository_catalog
from app.modules.repository import materializer as repository_materializer


@pytest.fixture
def catalog_env(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    db_path = tmp_path / "catalog.sqlite3"
    engine = create_sqlite_engine(f"sqlite:///{db_path}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    settings = get_settings()
    monkeypatch.setattr(settings, "_REPOSITORIES", {"test": os.fspath(repo)})
    monkeypatch.setattr(settings, "_DEFAULT_REPO_ID", "test")
    monkeypatch.setattr(repository_catalog, "SessionLocal", session_factory)
    monkeypatch.setattr(repository_materializer, "SessionLocal", session_factory)
    yield repo, session_factory
    engine.dispose()
