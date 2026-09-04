import hashlib
import json

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import create_app
from app.config import AppConfig
from app.models import Base, Collection, Issue, Media, Message
from app.modules.collection import service as collection_service
from app.modules.issue import service as issue_service


OPENAPI_SEMANTIC_SHA256 = "eae708bb6fffabcf55c972a9334c332b6fefdc8ebbaf86bd9bbe4fc8567d0b24"


def _normalize_openapi(value):
    """Canonicalize map and set-like list order without dropping contract data."""
    if isinstance(value, dict):
        return {key: _normalize_openapi(item) for key, item in sorted(value.items())}
    if isinstance(value, list):
        items = [_normalize_openapi(item) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    return value


def _contract_projection(schema):
    """Compare public wire shape, excluding descriptive OpenAPI metadata."""
    if isinstance(schema, dict):
        return {
            key: _contract_projection(value)
            for key, value in schema.items()
            if key not in {"description", "summary", "title"}
        }
    if isinstance(schema, list):
        return [_contract_projection(value) for value in schema]
    return schema


def _dereference(value, components):
    if isinstance(value, dict):
        ref = value.get("$ref")
        if ref and ref.startswith("#/components/schemas/"):
            return _dereference(components[ref.rsplit("/", 1)[-1]], components)
        return {key: _dereference(item, components) for key, item in value.items()}
    if isinstance(value, list):
        return [_dereference(item, components) for item in value]
    return value


def _test_session_factory(tmp_path):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'api.sqlite3'}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _record):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine, sessionmaker(autocommit=False, autoflush=False, bind=engine)


def test_factory_preserves_openapi_contract():
    schema = create_app(start_background_services=False, validate_runtime=False).openapi()
    resolved_paths = _dereference(schema["paths"], schema["components"]["schemas"])
    raw = json.dumps(
        _normalize_openapi(_contract_projection(resolved_paths)),
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode()
    assert hashlib.sha256(raw).hexdigest() == OPENAPI_SEMANTIC_SHA256


def test_factory_supports_isolated_http_database(tmp_path):
    engine, factory = _test_session_factory(tmp_path)
    app = create_app(
        session_factory=factory,
        start_background_services=False,
        validate_runtime=False,
    )
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        response = client.get("/messages")
        assert response.status_code == 200
        assert response.json() == {"items": [], "next_cursor": None, "has_more": False}
        assert app.state.background_services.started is False
    engine.dispose()


def test_message_http_contract_and_transaction(tmp_path):
    engine, factory = _test_session_factory(tmp_path)
    app = create_app(
        session_factory=factory, start_background_services=False, validate_runtime=False
    )
    with TestClient(app) as client:
        created = client.post(
            "/messages",
            json={"text": "contract", "files": [], "tag_ids": []},
        )
        assert created.status_code == 201
        message_id = created.json()["id"]
        assert created.json()["text"] == "contract"

        updated = client.patch(
            f"/messages/{message_id}",
            json={"text": "updated", "starred": True},
        )
        assert updated.status_code == 200
        assert updated.json()["text"] == "updated"
        assert updated.json()["starred"] is True

        assert client.get(f"/messages/{message_id}").status_code == 200
        assert client.delete(f"/messages/{message_id}").status_code == 204
        assert client.get(f"/messages/{message_id}").status_code == 404
    engine.dispose()


def test_sync_requires_cursor(tmp_path):
    engine, factory = _test_session_factory(tmp_path)
    app = create_app(
        session_factory=factory, start_background_services=False, validate_runtime=False
    )
    with TestClient(app) as client:
        response = client.get("/sync/changes")
        assert response.status_code == 410
        assert "since" in response.json()["detail"]
    engine.dispose()


def test_media_write_endpoints_commit_to_isolated_database(tmp_path):
    engine, factory = _test_session_factory(tmp_path)
    with factory() as db:
        db.add(Media(
            id=1, repo_id="test", file_path="one.jpg", file_hash="one",
            rating=0, starred=0, view_count=0,
        ))
        db.commit()
    app = create_app(
        session_factory=factory, start_background_services=False, validate_runtime=False
    )
    with TestClient(app) as client:
        starred = client.put("/media/1/starred", params={"starred": True})
        rating = client.put("/media/1/rating", params={"rating": 8})
        assert starred.status_code == 200
        assert starred.json() == {"starred": True}
        assert rating.status_code == 200
        assert rating.json()["rating"] == 8
    with factory() as db:
        media = db.get(Media, 1)
        assert media.starred == 1
        assert media.rating == 8
    engine.dispose()


def test_sync_apply_rolls_back_entire_failed_batch(tmp_path):
    engine, factory = _test_session_factory(tmp_path)
    app = create_app(
        session_factory=factory, start_background_services=False, validate_runtime=False
    )
    payload = {"changes": [
        {"entityType": "COLLECTION", "operation": "UPSERT", "entityId": 1,
         "payload": {"name": "duplicate"}},
        {"entityType": "COLLECTION", "operation": "UPSERT", "entityId": 2,
         "payload": {"name": "duplicate"}},
    ]}
    with TestClient(app) as client:
        response = client.post("/api/sync/apply", json=payload)
        assert response.status_code == 200
        assert response.json()["applied"] == 0
        assert response.json()["failed"] == 2
    with factory() as db:
        assert db.query(Collection).count() == 0
    engine.dispose()


def test_factory_instances_do_not_duplicate_routes():
    first = create_app(start_background_services=False, validate_runtime=False)
    second = create_app(start_background_services=False, validate_runtime=False)
    first_routes = [(route.path, tuple(route.methods or ())) for route in first.routes]
    second_routes = [(route.path, tuple(route.methods or ())) for route in second.routes]
    assert first_routes == second_routes


def test_factory_settings_select_an_isolated_database(tmp_path):
    data_root = tmp_path / "isolated-data"
    repository = tmp_path / "isolated-repo"
    data_root.mkdir()
    repository.mkdir()
    settings = AppConfig(
        data_root=str(data_root),
        repositories={"isolated": str(repository)},
        default_repo_id="isolated",
        load_repositories=False,
    )
    engine = create_engine(f"sqlite:///{data_root / 'db.sqlite3'}")
    Base.metadata.create_all(engine)
    engine.dispose()
    app = create_app(settings=settings, start_background_services=False, validate_runtime=False)
    with TestClient(app) as client:
        created = client.post("/messages", json={"text": "isolated", "files": [], "tag_ids": []})
        assert created.status_code == 201
    engine = create_engine(f"sqlite:///{data_root / 'db.sqlite3'}")
    with engine.connect() as connection:
        assert connection.exec_driver_sql("SELECT text FROM message").scalar_one() == "isolated"
    engine.dispose()


def test_router_registry_includes_todos_without_duplicates():
    app = create_app(start_background_services=False, validate_runtime=False)
    routes = [
        (method, route.path)
        for route in app.routes
        for method in (route.methods or ())
        if method not in {"HEAD", "OPTIONS"}
    ]
    assert len(routes) == len(set(routes))
    assert {
        ("GET", "/todos"),
        ("POST", "/todos"),
        ("PATCH", "/todos/{todo_id}"),
        ("PATCH", "/todos/{todo_id}/move"),
        ("DELETE", "/todos/{todo_id}"),
    }.issubset(set(routes))


def test_collection_use_case_rolls_back_failed_commit(tmp_path, monkeypatch):
    engine, factory = _test_session_factory(tmp_path)
    with factory() as db:
        original_commit = db.commit

        def fail_commit():
            raise RuntimeError("commit failed")

        monkeypatch.setattr(db, "commit", fail_commit)
        try:
            collection_service.create(db, "must-rollback", None)
        except RuntimeError:
            pass
        else:
            raise AssertionError("commit failure was not propagated")
        monkeypatch.setattr(db, "commit", original_commit)
        assert db.query(Collection).filter_by(name="must-rollback").first() is None
    engine.dispose()


def test_issue_message_count_map_returns_counts(tmp_path):
    engine, factory = _test_session_factory(tmp_path)
    with factory() as db:
        issue = Issue(title="tracked", status="doing", position=0)
        db.add(issue)
        db.flush()
        db.add(Message(text="linked", issue_id=issue.id))
        db.commit()
        assert issue_service.message_count_map(db, [issue.id]) == {issue.id: 1}
    engine.dispose()
