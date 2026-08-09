from datetime import datetime

import pytest
from fastapi import HTTPException

from app.models import Media
from app.models.repository_catalog import RepositoryFile, RepositoryFolder
from app.routers.media import get_media
from app.routers.repositories import list_duplicate_files
from app.services.duplicate_file_service import _safe_repository_path, delete_physical_files


def add_media(db, media_id, repo_id="test", file_path=None):
    media = Media(
        id=media_id,
        repo_id=repo_id,
        file_path=file_path or f"{media_id}-a.jpg",
        file_hash=f"hash-{media_id}",
        file_size=10,
        mime_type="image/jpeg",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    db.add(media)
    db.flush()
    return media


def add_file(db, repo, folder, file_id, media_id, rel_path, status="done", create=True):
    if create:
        path = repo / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"same")
    row = RepositoryFile(
        id=file_id,
        repo_id="test",
        folder_id=folder.id,
        rel_path=rel_path,
        name=rel_path.rsplit("/", 1)[-1],
        media_type="image",
        file_size=4,
        mtime=1,
        media_id=media_id,
        materialize_status=status,
    )
    db.add(row)
    db.flush()
    return row


def setup_group(db, repo, media_id=1):
    folder = RepositoryFolder(repo_id="test", rel_path="", name="test")
    db.add(folder)
    db.flush()
    media = add_media(db, media_id)
    first = add_file(db, repo, folder, 1, media_id, f"{media_id}-a.jpg")
    second = add_file(db, repo, folder, 2, media_id, f"{media_id}-b.jpg")
    db.commit()
    return media, first, second, folder


def test_duplicate_groups_include_only_completed_copies(catalog_env):
    repo, session_factory = catalog_env
    with session_factory() as db:
        media, _, _, folder = setup_group(db, repo)
        add_media(db, 2)
        add_file(db, repo, folder, 3, 2, "2-a.jpg")
        add_file(db, repo, folder, 4, 2, "2-b.jpg", status="pending")
        db.commit()

        result = list_duplicate_files(cursor=None, limit=20, db=db)
        assert [group.media_id for group in result.items] == [media.id]
        assert len(result.items[0].files) == 2
        assert [file.is_canonical for file in result.items[0].files] == [True, False]


def test_delete_canonical_repoints_media_and_preserves_logical_row(catalog_env):
    repo, session_factory = catalog_env
    with session_factory() as db:
        media, first, second, _ = setup_group(db, repo)
        result = delete_physical_files(db, media.id, [first.id])

        db.refresh(media)
        assert result["deleted_ids"] == [first.id]
        assert result["remaining_count"] == 1
        assert (media.repo_id, media.file_path) == (second.repo_id, second.rel_path)
        assert db.get(Media, media.id) is not None
        assert not (repo / "1-a.jpg").exists()
        assert (repo / "1-b.jpg").exists()


def test_delete_all_copies_keeps_media_and_historical_canonical(catalog_env):
    repo, session_factory = catalog_env
    with session_factory() as db:
        media, first, second, _ = setup_group(db, repo)
        result = delete_physical_files(db, media.id, [first.id, second.id])

        db.refresh(media)
        assert result["remaining_count"] == 0
        assert result["canonical_available"] is False
        assert media.file_path == "1-a.jpg"
        assert db.query(RepositoryFile).filter_by(media_id=media.id).count() == 0

        missing = get_media(
            cursor=None,
            direction=None,
            limit=20,
            message_id=None,
            message_ids=None,
            starred=None,
            type=None,
            tag_id=None,
            collection_id=None,
            has_physical_file=False,
            db=db,
        )
        assert [item.id for item in missing.items] == [media.id]


def test_missing_file_cleans_catalog_row(catalog_env):
    repo, session_factory = catalog_env
    with session_factory() as db:
        media, first, _, _ = setup_group(db, repo)
        (repo / first.rel_path).unlink()
        result = delete_physical_files(db, media.id, [first.id])
        assert result["missing_ids"] == [first.id]
        assert db.get(RepositoryFile, first.id) is None


def test_delete_rejects_stale_cross_group_and_unsafe_paths(catalog_env):
    repo, session_factory = catalog_env
    with session_factory() as db:
        media, first, _, folder = setup_group(db, repo)
        add_media(db, 2)
        other = add_file(db, repo, folder, 3, 2, "2-a.jpg")
        db.commit()

        with pytest.raises(HTTPException):
            delete_physical_files(db, media.id, [first.id, other.id])
        with pytest.raises(ValueError):
            _safe_repository_path("test", "../outside.jpg")
        with pytest.raises(ValueError):
            _safe_repository_path("missing", "x.jpg")
