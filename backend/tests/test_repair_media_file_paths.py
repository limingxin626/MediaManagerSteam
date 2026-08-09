from datetime import datetime

from app.models import Media
from app.models.repository_catalog import RepositoryFile, RepositoryFolder
from scripts.repair_media_file_paths import repair_media_file_paths


def add_media(db, media_id, file_path, *, video_media_id=None):
    media = Media(
        id=media_id,
        repo_id="test",
        file_path=file_path,
        file_hash=f"hash-{media_id}",
        file_size=1,
        mime_type="image/jpeg",
        video_media_id=video_media_id,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    db.add(media)
    db.flush()
    return media


def add_repository_file(db, folder, file_id, media_id, rel_path, status="done"):
    row = RepositoryFile(
        id=file_id,
        repo_id="test",
        folder_id=folder.id,
        rel_path=rel_path,
        name=rel_path,
        media_type="image",
        file_size=1,
        mtime=1,
        media_id=media_id,
        materialize_status=status,
    )
    db.add(row)
    db.flush()
    return row


def seed_cases(session_factory):
    with session_factory() as db:
        folder = RepositoryFolder(repo_id="test", rel_path="", name="test")
        db.add(folder)
        db.flush()

        add_media(db, 1, "valid.jpg")
        add_repository_file(db, folder, 1, 1, "valid.jpg")

        add_media(db, 2, "stale.jpg")
        add_repository_file(db, folder, 2, 2, "replacement-b.jpg")
        add_repository_file(db, folder, 3, 2, "replacement-a.jpg")

        add_media(db, 3, "missing.jpg")
        add_repository_file(db, folder, 4, 3, "pending.jpg", status="pending")

        add_media(db, 4, "preview.jpg", video_media_id=1)
        db.commit()


def test_dry_run_reports_without_writing(catalog_env):
    _, session_factory = catalog_env
    seed_cases(session_factory)

    stats = repair_media_file_paths(session_factory=session_factory)

    assert stats == {
        "total": 3,
        "valid": 1,
        "invalid": 2,
        "repairable": 1,
        "repaired": 0,
        "without_copy": 1,
        "repair_samples": [{
            "id": 2,
            "old": "test/stale.jpg",
            "new": "test/replacement-a.jpg",
        }],
        "without_copy_samples": [{
            "id": 3,
            "repo_id": "test",
            "file_path": "missing.jpg",
        }],
    }
    with session_factory() as db:
        assert db.get(Media, 2).file_path == "stale.jpg"


def test_apply_repairs_only_media_with_completed_copy(catalog_env):
    _, session_factory = catalog_env
    seed_cases(session_factory)

    stats = repair_media_file_paths(apply=True, session_factory=session_factory)

    assert stats["repaired"] == 1
    with session_factory() as db:
        assert db.get(Media, 1).file_path == "valid.jpg"
        assert db.get(Media, 2).file_path == "replacement-a.jpg"
        assert db.get(Media, 3).file_path == "missing.jpg"
        assert db.get(Media, 4).file_path == "preview.jpg"