import os

from app.models import Media, RepositoryFile, RepositoryFolder
from app.services import repository_catalog, repository_materializer


def test_scan_preserves_empty_folders_and_only_supported_files(catalog_env):
    repo, session_factory = catalog_env
    (repo / "empty").mkdir()
    (repo / "photo.jpg").write_bytes(b"image")
    (repo / "movie.mkv").write_bytes(b"unsupported")

    result = repository_catalog.rescan("test")

    assert result["inserted"] == 3  # root, empty folder, supported file
    with session_factory() as db:
        assert {row.rel_path for row in db.query(RepositoryFolder)} == {"", "empty"}
        assert [row.rel_path for row in db.query(RepositoryFile)] == ["photo.jpg"]


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
