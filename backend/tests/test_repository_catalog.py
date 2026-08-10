import os
from io import BytesIO

import pytest

from app.models import Media, Message, MessageFolder, MessageMedia, RepositoryFile, RepositoryFolder
from app.services import repository_catalog, repository_materializer
from app.services.folder_message_service import (
    backfill_existing_folder_messages,
    store_file_in_primary_folder,
)
from app.services.message_service import add_media_to_message_service, update_message_service
from app.routers.message import _build_detail_response


def test_scan_skips_empty_folders_and_only_catalogs_supported_files(catalog_env):
    repo, session_factory = catalog_env
    (repo / "empty").mkdir()
    (repo / "photo.jpg").write_bytes(b"image")
    (repo / "movie.mkv").write_bytes(b"unsupported")

    result = repository_catalog.rescan("test")

    assert result["inserted"] == 2  # root and supported file
    with session_factory() as db:
        assert {row.rel_path for row in db.query(RepositoryFolder)} == {""}
        assert [row.rel_path for row in db.query(RepositoryFile)] == ["photo.jpg"]
        assert db.query(MessageFolder).count() == 0


def test_changed_path_detaches_old_media_and_requeues(catalog_env):
    repo, session_factory = catalog_env
    source = repo / "photo.jpg"
    source.write_bytes(b"old")
    old_stat = source.stat()
    with session_factory() as db:
        media = Media(repo_id="test", file_path="photo.jpg", file_hash="old-hash", file_size=3)
        db.add(media)
        db.commit()

    repository_catalog.rescan("test")
    source.write_bytes(b"different bytes")
    os.utime(source, (old_stat.st_atime, old_stat.st_mtime + 5))
    repository_catalog.rescan("test")

    with session_factory() as db:
        row = db.query(RepositoryFile).one()
        assert row.media_id is None
        assert row.materialize_status == "pending"


def test_fk_cleared_done_row_becomes_pending(catalog_env):
    repo, session_factory = catalog_env
    (repo / "photo.jpg").write_bytes(b"image")
    with session_factory() as db:
        media = Media(repo_id="test", file_path="photo.jpg", file_hash="hash", file_size=5)
        db.add(media)
        db.commit()
    repository_catalog.rescan("test")

    with session_factory() as db:
        media = db.query(Media).one()
        db.delete(media)
        db.commit()
    repository_catalog.rescan("test")

    with session_factory() as db:
        row = db.query(RepositoryFile).one()
        assert row.media_id is None
        assert row.materialize_status == "pending"


def test_offline_scan_preserves_catalog(catalog_env):
    repo, session_factory = catalog_env
    (repo / "photo.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")
    repo.rename(repo.with_name("offline"))

    result = repository_catalog.rescan("test")

    assert result["offline"] == ["test"]
    with session_factory() as db:
        assert db.query(RepositoryFile).count() == 1


def test_folder_rename_preserves_catalog_identity(catalog_env):
    repo, session_factory = catalog_env
    original = repo / "original"
    original.mkdir()
    (original / "keep.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        folder_id = db.query(RepositoryFolder).filter_by(rel_path="original").one().id

    original.rename(repo / "renamed")
    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(RepositoryFolder).filter_by(rel_path="renamed").one()
        assert folder.id == folder_id
        assert db.query(RepositoryFolder).filter_by(rel_path="original").count() == 0


def test_folder_message_media_is_derived_from_catalog(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "photo.jpg").write_bytes(b"image")
    with session_factory() as db:
        db.add(Media(
            repo_id="test",
            file_path="album/photo.jpg",
            file_hash="photo-hash",
            file_size=5,
        ))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(RepositoryFolder).filter_by(rel_path="album").one()
        link = db.query(MessageFolder).filter_by(repository_folder_id=folder.id).one()
        relation = db.query(MessageMedia).filter_by(message_id=link.message_id).one()
        assert db.query(Message).filter_by(id=link.message_id).count() == 1
        assert relation.media_id == db.query(Media).one().id
        assert relation.position == 0


def test_removed_file_is_removed_from_derived_message_only(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    source = album / "photo.jpg"
    source.write_bytes(b"image")
    with session_factory() as db:
        db.add(Media(
            repo_id="test",
            file_path="album/photo.jpg",
            file_hash="photo-hash",
            file_size=5,
        ))
        db.commit()
    repository_catalog.rescan("test")

    source.unlink()
    repository_catalog.rescan("test")

    with session_factory() as db:
        assert db.query(MessageMedia).count() == 0
        assert db.query(Media).count() == 1


def test_folder_becoming_empty_removes_folder_and_message(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    source = album / "photo.jpg"
    source.write_bytes(b"image")
    with session_factory() as db:
        db.add(Media(
            repo_id="test",
            file_path="album/photo.jpg",
            file_hash="empty-folder-photo-hash",
            file_size=5,
        ))
        db.commit()
    repository_catalog.rescan("test")

    source.unlink()
    repository_catalog.rescan("test")

    with session_factory() as db:
        assert db.query(RepositoryFolder).filter_by(rel_path="album").count() == 0
        assert db.query(MessageFolder).count() == 0
        assert db.query(Message).count() == 0
        assert db.query(Media).count() == 1


def test_backfill_reuses_existing_message_and_removes_generated_duplicate(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "photo.jpg").write_bytes(b"image")
    with session_factory() as db:
        media = Media(
            repo_id="test",
            file_path="album/photo.jpg",
            file_hash="backfill-photo-hash",
            file_size=5,
        )
        message = Message(text="existing album")
        db.add_all([media, message])
        db.flush()
        db.add(MessageMedia(message_id=message.id, media_id=media.id, position=0))
        db.commit()
        existing_message_id = message.id

    repository_catalog.rescan("test")

    with session_factory() as db:
        assert db.query(Message).count() == 2
        dry_run = backfill_existing_folder_messages(db, apply=False)
        assert dry_run["matched_folders"] == 1
        assert dry_run["matched_messages"] == 1
        assert db.query(MessageFolder).one().message_id != existing_message_id
        db.rollback()

    with session_factory() as db:
        applied = backfill_existing_folder_messages(db, apply=True)
        db.commit()
        assert applied["deleted_generated_messages"] == 1
        assert db.query(MessageFolder).one().message_id == existing_message_id
        assert db.query(Message).count() == 1
        assert db.query(MessageMedia).filter_by(message_id=existing_message_id).count() == 1


def test_backfill_does_not_replace_edited_folder_message(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "photo.jpg").write_bytes(b"image")
    with session_factory() as db:
        media = Media(
            repo_id="test",
            file_path="album/photo.jpg",
            file_hash="protected-backfill-photo-hash",
            file_size=5,
        )
        legacy = Message(text="legacy")
        db.add_all([media, legacy])
        db.flush()
        db.add(MessageMedia(message_id=legacy.id, media_id=media.id, position=0))
        db.commit()
        legacy_id = legacy.id

    repository_catalog.rescan("test")
    with session_factory() as db:
        link = db.query(MessageFolder).one()
        generated_id = link.message_id
        link.message.text = "edited after migration"
        db.commit()

    with session_factory() as db:
        stats = backfill_existing_folder_messages(db, apply=True)
        db.commit()
        assert stats["ambiguous_folders"] == 1
        assert db.query(MessageFolder).one().message_id == generated_id
        assert db.get(Message, legacy_id) is not None


def test_folder_backed_message_rejects_direct_media_writes(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        message_id = db.query(MessageFolder).one().message_id
        with pytest.raises(ValueError, match="Folder-backed"):
            update_message_service(db, message_id, media_order=[], commit=False)
        with pytest.raises(ValueError, match="Folder-backed"):
            add_media_to_message_service(db, message_id, [], commit=False)


def test_message_detail_includes_repository_folders(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        message = db.query(Message).join(MessageFolder).one()
        response = _build_detail_response(db, message, media_limit=None)
        assert len(response.folders) == 1
        assert response.folders[0].repo_id == "test"
        assert response.folders[0].rel_path == "album"
        assert response.folders[0].role == "PRIMARY"


def test_store_file_in_message_primary_folder(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        message_id = db.query(MessageFolder).one().message_id
        repo_id, destination = store_file_in_primary_folder(
            db,
            message_id,
            "photo.jpg",
            BytesIO(b"image"),
        )

    assert repo_id == "test"
    assert destination == os.fspath(album / "photo.jpg")
    assert (album / "photo.jpg").read_bytes() == b"image"

    repository_catalog.rescan("test")
    with session_factory() as db:
        row = db.query(RepositoryFile).filter_by(rel_path="album/photo.jpg").one()
        assert row.materialize_status == "pending"


def test_worker_materializes_and_copies_hdr_metadata(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    source = repo / "movie.mp4"
    source.write_bytes(b"video")
    repository_catalog.rescan("test")

    def fake_process(db, path, commit=False):
        media = Media(repo_id="test", file_path="movie.mp4", file_hash="video-hash", file_size=5)
        db.add(media)
        db.flush()
        return {"media": media, "is_new": True, "media_info": {
            "is_hdr": 1, "color_transfer": "smpte2084",
        }}

    monkeypatch.setattr(repository_materializer.media_service, "process_file", fake_process)
    assert repository_materializer._process_batch() == 1

    with session_factory() as db:
        row = db.query(RepositoryFile).one()
        assert row.materialize_status == "done"
        assert row.media_id is not None
        assert row.is_hdr == 1
        assert row.color_transfer == "smpte2084"


def test_worker_updates_folder_backed_message(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    source = album / "movie.mp4"
    source.write_bytes(b"video")
    repository_catalog.rescan("test")

    def fake_process(db, path, commit=False):
        media = Media(
            repo_id="test",
            file_path="album/movie.mp4",
            file_hash="album-video-hash",
            file_size=5,
        )
        db.add(media)
        db.flush()
        return {"media": media, "is_new": True, "media_info": {}}

    monkeypatch.setattr(repository_materializer.media_service, "process_file", fake_process)
    assert repository_materializer._process_batch() == 1

    with session_factory() as db:
        link = db.query(MessageFolder).join(RepositoryFolder).filter(
            RepositoryFolder.rel_path == "album",
        ).one()
        relation = db.query(MessageMedia).filter_by(message_id=link.message_id).one()
        assert relation.media_id == db.query(Media).one().id


def test_folder_rename_promotes_media_canonical_path(catalog_env, monkeypatch):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    source = album / "photo.jpg"
    source.write_bytes(b"image")
    with session_factory() as db:
        db.add(Media(
            repo_id="test",
            file_path="album/photo.jpg",
            file_hash="photo-hash",
            file_size=5,
        ))
        db.commit()
    repository_catalog.rescan("test")

    album.rename(repo / "renamed")
    repository_catalog.rescan("test")

    def fake_process(db, path, commit=False):
        return {"media": db.query(Media).one(), "is_new": False, "media_info": {}}

    monkeypatch.setattr(repository_materializer.media_service, "process_file", fake_process)
    assert repository_materializer._process_batch() == 1

    with session_factory() as db:
        media = db.query(Media).one()
        assert media.repo_id == "test"
        assert media.file_path == "renamed/photo.jpg"
        link = db.query(MessageFolder).join(RepositoryFolder).filter(
            RepositoryFolder.rel_path == "renamed",
        ).one()
        assert db.query(MessageMedia).filter_by(
            message_id=link.message_id,
            media_id=media.id,
        ).count() == 1
