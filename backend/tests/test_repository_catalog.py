import os
from io import BytesIO

import pytest

from app.models import Folder, FolderLocation, Media, Message, MessageFolder, RepositoryFile, RepositoryFolder
from app.routers.folder import get_folder
from app.services import repository_catalog, repository_materializer
from app.services.folder_service import store_file_in_primary_folder
from app.routers.message import _build_detail_query, _execute_like_search


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


def test_non_media_folder_does_not_create_message(catalog_env):
    repo, session_factory = catalog_env
    notes = repo / "notes"
    notes.mkdir()
    (notes / "readme.txt").write_text("not media", encoding="utf-8")

    repository_catalog.rescan("test")

    with session_factory() as db:
        assert db.query(RepositoryFolder).filter_by(rel_path="notes").count() == 1
        assert db.query(RepositoryFile).count() == 0
        assert db.query(MessageFolder).count() == 0
        assert db.query(Message).count() == 0


def test_removing_last_media_deletes_logical_folder_when_other_files_remain(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    media_file = album / "photo.jpg"
    media_file.write_bytes(b"image")
    (album / "readme.txt").write_text("keep folder cataloged", encoding="utf-8")

    repository_catalog.rescan("test")
    with session_factory() as db:
        assert db.query(Folder).count() == 1

    media_file.unlink()
    repository_catalog.rescan("test")

    with session_factory() as db:
        assert db.query(RepositoryFolder).filter_by(rel_path="album").count() == 1
        assert db.query(RepositoryFile).count() == 0
        assert db.query(Folder).count() == 0


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


def test_folder_media_is_read_directly_from_catalog(catalog_env):
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
        location = db.query(FolderLocation).filter_by(repository_folder_id=folder.id).one()
        file = db.query(RepositoryFile).filter_by(folder_id=folder.id).one()
        response = get_folder(location.folder_id, db)

        assert file.media_id == db.query(Media).one().id
        assert response.media_count == 1
        assert [item.media_id for item in response.files] == [file.media_id]


def test_removed_file_removes_logical_folder_but_preserves_media(catalog_env):
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
        assert db.query(Folder).count() == 0
        assert db.query(Media).count() == 1


def test_folder_becoming_empty_removes_catalog_and_logical_folder(catalog_env):
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
        assert db.query(Folder).count() == 0
        assert db.query(Media).count() == 1


def test_ordinary_message_query_excludes_folder_backed_messages(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        ordinary = Message(text="ordinary")
        db.add(ordinary)
        db.commit()

        rows = _build_detail_query(db, None, None, None, None).all()

        assert [row.id for row in rows] == [ordinary.id]


def test_message_like_search_excludes_folder_backed_messages(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        ordinary = Message(text="album note")
        db.add(ordinary)
        db.commit()

        rows = _execute_like_search(db, "album", None, None, None, None, 20)

        assert [row.id for row in rows] == [ordinary.id]


def test_scan_creates_independent_folder_with_catalog_files(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")

    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(Folder).one()
        location = db.query(FolderLocation).one()
        response = get_folder(folder.id, db)

        assert location.repository_folder.rel_path == "album"
        assert response.name == "album"
        assert [item.rel_path for item in response.files] == ["album/existing.jpg"]


def test_folder_name_follows_physical_folder_rename(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        folder_id = db.query(Folder).one().id

    album.rename(repo / "renamed")
    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(Folder).one()
        response = get_folder(folder.id, db)

        assert folder.id == folder_id
        assert response.name == "renamed"
        assert response.primary_folder_path == "renamed"


def test_store_file_in_folder_primary_location(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "existing.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        folder_id = db.query(Folder).one().id
        repo_id, destination = store_file_in_primary_folder(
            db,
            folder_id,
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


def test_worker_updates_folder_catalog_media(catalog_env, monkeypatch):
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
        folder = db.query(Folder).one()
        file = db.query(RepositoryFile).filter_by(rel_path="album/movie.mp4").one()
        response = get_folder(folder.id, db)

        assert file.media_id == db.query(Media).one().id
        assert response.media_count == 1


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
        folder = db.query(Folder).one()
        file = db.query(RepositoryFile).filter_by(rel_path="renamed/photo.jpg").one()
        response = get_folder(folder.id, db)

        assert file.media_id == media.id
        assert response.name == "renamed"
        assert response.media_count == 1
