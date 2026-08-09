import sqlite3
from datetime import datetime

from app.models import Media, RepositoryFile, RepositoryFolder
from scripts import repair_media_dates


def add_media(session_factory, **overrides):
    values = {
        "id": 1,
        "repo_id": "test",
        "file_path": "photo.jpg",
        "file_hash": "hash",
        "file_size": 5,
        "mime_type": "image/jpeg",
    }
    values.update(overrides)
    with session_factory() as db:
        db.add(Media(**values))
        db.commit()


def test_repair_dry_run_does_not_write_and_apply_repairs(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    (repo / "photo.jpg").write_bytes(b"image")
    expected_created_at = datetime(2020, 5, 6, 7, 8, 9)
    monkeypatch.setattr(repair_media_dates, "get_file_created_at", lambda _: expected_created_at)
    add_media(session_factory, taken_at=datetime(1970, 1, 1, 12))

    dry_run = repair_media_dates.repair_media_dates(
        apply=False,
        session_factory=session_factory,
    )
    assert dry_run["taken_at_present"] == 1
    assert dry_run["taken_at_missing"] == 0
    assert dry_run["epoch_taken_at"] == 1
    assert dry_run["file_created_at_present"] == 0
    assert dry_run["file_created_at_missing"] == 1
    assert dry_run["file_created_at_filled"] == 1
    with session_factory() as db:
        media = db.get(Media, 1)
        assert media.taken_at == datetime(1970, 1, 1, 12)
        assert media.file_created_at is None

    applied = repair_media_dates.repair_media_dates(
        apply=True,
        session_factory=session_factory,
    )
    assert applied["epoch_taken_at"] == 1
    assert applied["file_created_at_filled"] == 1
    with session_factory() as db:
        media = db.get(Media, 1)
        assert media.taken_at is None
        assert media.file_created_at == expected_created_at


def test_default_mode_preserves_existing_value(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    (repo / "photo.jpg").write_bytes(b"image")
    old_value = datetime(2024, 1, 1)
    add_media(session_factory, file_created_at=old_value)
    called = False

    def get_date(_):
        nonlocal called
        called = True
        return datetime(2020, 1, 1)

    monkeypatch.setattr(repair_media_dates, "get_file_created_at", get_date)
    stats = repair_media_dates.repair_media_dates(
        apply=True,
        session_factory=session_factory,
    )
    assert called is False
    assert stats["file_created_at_present"] == 1
    assert stats["file_created_at_missing"] == 0
    assert stats["file_created_at_corrected"] == 0
    with session_factory() as db:
        assert db.get(Media, 1).file_created_at == old_value


def test_overwrite_dry_run_and_apply_correct_existing_value(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    (repo / "photo.jpg").write_bytes(b"image")
    old_value = datetime(2024, 1, 1)
    new_value = datetime(2020, 1, 1)
    add_media(session_factory, file_created_at=old_value)
    monkeypatch.setattr(repair_media_dates, "get_file_created_at", lambda _: new_value)

    dry_run = repair_media_dates.repair_media_dates(
        overwrite_existing=True,
        session_factory=session_factory,
    )
    assert dry_run["file_created_at_corrected"] == 1
    assert dry_run["correction_samples"][0]["old"] == "2024-01-01 00:00:00"
    with session_factory() as db:
        assert db.get(Media, 1).file_created_at == old_value

    applied = repair_media_dates.repair_media_dates(
        apply=True,
        overwrite_existing=True,
        session_factory=session_factory,
    )
    assert applied["file_created_at_corrected"] == 1
    with session_factory() as db:
        assert db.get(Media, 1).file_created_at == new_value

    unchanged = repair_media_dates.repair_media_dates(
        overwrite_existing=True,
        session_factory=session_factory,
    )
    assert unchanged["file_created_at_corrected"] == 0
    assert unchanged["file_created_at_unchanged"] == 1


def test_overwrite_reports_missing_file(catalog_env):
    _, session_factory = catalog_env
    add_media(session_factory, file_created_at=datetime(2024, 1, 1))

    stats = repair_media_dates.repair_media_dates(
        overwrite_existing=True,
        session_factory=session_factory,
    )
    assert stats["missing_file"] == 1
    assert stats["missing_file_samples"][0]["id"] == 1


def test_stale_canonical_path_falls_back_to_completed_physical_copy(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    physical_path = repo / "available.jpg"
    physical_path.write_bytes(b"image")
    expected_created_at = datetime(2021, 2, 3, 4, 5, 6)
    monkeypatch.setattr(repair_media_dates, "get_file_created_at", lambda _: expected_created_at)
    add_media(session_factory, file_path="stale.jpg")
    with session_factory() as db:
        folder = RepositoryFolder(repo_id="test", rel_path="", name="test")
        db.add(folder)
        db.flush()
        db.add(RepositoryFile(
            repo_id="test",
            folder_id=folder.id,
            rel_path="available.jpg",
            name="available.jpg",
            media_type="image",
            file_size=5,
            mtime=1,
            media_id=1,
            materialize_status="done",
        ))
        db.commit()

    stats = repair_media_dates.repair_media_dates(
        apply=True,
        session_factory=session_factory,
    )

    assert stats["physical_copy_fallback"] == 1
    assert stats["missing_file"] == 0
    assert stats["file_created_at_filled"] == 1
    assert stats["physical_copy_fallback_samples"][0]["physical_path"] == str(physical_path)
    with session_factory() as db:
        media = db.get(Media, 1)
        assert media.file_created_at == expected_created_at
        assert media.file_path == "stale.jpg"


def test_backup_database_creates_valid_copy(tmp_path):
    db_path = tmp_path / "db.sqlite3"
    with sqlite3.connect(db_path) as db:
        db.execute("create table sample (value text)")
        db.execute("insert into sample values ('ok')")

    backup_path = repair_media_dates.backup_database(str(db_path))

    with sqlite3.connect(backup_path) as backup:
        assert backup.execute("select value from sample").fetchone() == ("ok",)
