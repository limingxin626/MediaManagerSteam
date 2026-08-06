import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.config import config
from app.models import Base
from app.services import repository_catalog, repository_materializer


@pytest.fixture
def catalog_env(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    db_path = tmp_path / "catalog.sqlite3"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr(type(config), "_REPOSITORIES", {"test": os.fspath(repo)})
    monkeypatch.setattr(type(config), "_DEFAULT_REPO_ID", "test")
    monkeypatch.setattr(repository_catalog, "SessionLocal", session_factory)
    monkeypatch.setattr(repository_materializer, "SessionLocal", session_factory)
    yield repo, session_factory
    engine.dispose()
