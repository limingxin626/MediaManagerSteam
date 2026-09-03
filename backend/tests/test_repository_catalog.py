import os
from io import BytesIO

import pytest

from app.models import Folder, FolderLocation, Media, Message, MessageFolder, RepositoryFile, RepositoryFolder, Tag
from app.modules.repository.folder_queries import get_folder, list_folder_tags, list_folders
from app.modules.repository import catalog as repository_catalog
from app.modules.repository import materializer as repository_materializer
from app.modules.repository.folder_service import store_file_in_primary_folder
from app.modules.message.router import _build_detail_query
from app.modules.message.queries import _like_search


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
            starred=1,
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
        assert response.files[0].starred is True
        assert response.kind == "gallery"
        assert [item.media_id for item in response.gallery] == [file.media_id]
        assert response.gallery[0].starred is True
        assert response.primary_entry_id is None


def test_scan_persists_folder_kind_on_logical_folder(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "photo.jpg").write_bytes(b"image")
    with session_factory() as db:
        db.add(Media(repo_id="test", file_path="album/photo.jpg", file_hash="p-hash", file_size=5))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(RepositoryFolder).filter_by(rel_path="album").one()
        location = db.query(FolderLocation).filter_by(repository_folder_id=folder.id).one()
        logical = db.get(Folder, location.folder_id)
        # The scan must persist the computed kind so /folders?kind= can filter.
        assert logical.kind == "gallery"


def test_scan_persists_movie_kind_for_cover_only_folder(catalog_env):
    repo, session_factory = catalog_env
    title = repo / "SNIS-752"
    title.mkdir()
    names = ["SNIS-752-fanart.jpg", "SNIS-752-poster.jpg", "fanart1.jpg"]
    for index, name in enumerate(names):
        (title / name).write_bytes(name.encode())
    with session_factory() as db:
        for index, name in enumerate(names):
            db.add(Media(repo_id="test", file_path=f"SNIS-752/{name}", file_hash=f"h{index}", file_size=len(name)))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(RepositoryFolder).filter_by(rel_path="SNIS-752").one()
        location = db.query(FolderLocation).filter_by(repository_folder_id=folder.id).one()
        logical = db.get(Folder, location.folder_id)
        assert logical.kind == "movie"


def test_folder_response_includes_named_cover_files(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    names = ["a.jpg", "b.jpg", "c.jpg", "d.jpg", "fanart.jpg", "poster.jpg"]
    for name in names:
        (album / name).write_bytes(name.encode())

    with session_factory() as db:
        for index, name in enumerate(names):
            db.add(Media(
                repo_id="test",
                file_path=f"album/{name}",
                file_hash=f"cover-{index}",
                file_size=len(name),
            ))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(RepositoryFolder).filter_by(rel_path="album").one()
        location = db.query(FolderLocation).filter_by(repository_folder_id=folder.id).one()
        response = get_folder(location.folder_id, db)

        assert [item.name for item in response.preview_files] == names[:4]
        assert response.fanart_file is not None
        assert response.fanart_file.name == "fanart.jpg"
        assert response.poster_file is not None
        assert response.poster_file.name == "poster.jpg"


def test_prefixed_covers_and_numbered_fanart_previews(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    names = ["Movie.mp4", "Movie-poster.jpg", "Movie-fanart.jpg",
             "Movie-fanart1.jpg", "Movie-fanart2.jpg", "photo.jpg"]
    for name in names:
        (album / name).write_bytes(name.encode())

    with session_factory() as db:
        for index, name in enumerate(names):
            db.add(Media(
                repo_id="test",
                file_path=f"album/{name}",
                file_hash=f"prefixed-{index}",
                file_size=len(name),
                mime_type="video/mp4" if name.endswith(".mp4") else "image/jpeg",
            ))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(RepositoryFolder).filter_by(rel_path="album").one()
        location = db.query(FolderLocation).filter_by(repository_folder_id=folder.id).one()
        response = get_folder(location.folder_id, db)

        # 标题前缀的封面应被识别为主封面
        assert response.fanart_file is not None
        assert response.fanart_file.name == "Movie-fanart.jpg"
        assert response.poster_file is not None
        assert response.poster_file.name == "Movie-poster.jpg"
        # 编号 fanart 作为 previews(章节条),poster 编号/普通图不进
        preview_names = {(item.name, item.source) for item in response.previews}
        assert ("Movie-fanart1.jpg", "kodi") in preview_names
        assert ("Movie-fanart2.jpg", "kodi") in preview_names
        assert all(item.name != "photo.jpg" for item in response.previews)


def test_folder_detail_includes_named_and_video_child_previews(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    names = ["movie.mp4", "preview-01.jpg", "Preivew_02.png", "photo.jpg"]
    for name in names:
        (album / name).write_bytes(name.encode())

    with session_factory() as db:
        media_by_name = {}
        for index, name in enumerate(names):
            media = Media(
                repo_id="test",
                file_path=f"album/{name}",
                file_hash=f"folder-preview-{index}",
                file_size=len(name),
                mime_type="video/mp4" if name.endswith(".mp4") else "image/jpeg",
                starred=1 if name == "preview-01.jpg" else 0,
            )
            db.add(media)
            media_by_name[name] = media
        db.flush()
        generated = Media(
            repo_id="uploads",
            file_path="preview/generated.jpg",
            file_hash="generated-folder-preview",
            file_size=9,
            mime_type="image/jpeg",
            video_media_id=media_by_name["movie.mp4"].id,
            frame_ms=2500,
            starred=1,
        )
        db.add(generated)
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        folder = db.query(RepositoryFolder).filter_by(rel_path="album").one()
        location = db.query(FolderLocation).filter_by(repository_folder_id=folder.id).one()
        response = get_folder(location.folder_id, db)

        assert [(item.name, item.source) for item in response.previews] == [
            ("Preivew_02.png", "kodi"),
            ("preview-01.jpg", "kodi"),
            ("generated.jpg", "video"),
        ]
        assert response.previews[-1].video_media_id is not None
        assert response.previews[-1].frame_ms == 2500
        assert [item.starred for item in response.previews] == [False, True, True]
        assert all(item.name != "photo.jpg" for item in response.previews)


def test_folder_response_prefers_primary_kodi_covers(catalog_env):
    repo, session_factory = catalog_env
    album = repo / "album"
    album.mkdir()
    (album / "fanart.jpg").write_bytes(b"primary")

    with session_factory() as db:
        db.add(Media(
            repo_id="test",
            file_path="album/fanart.jpg",
            file_hash="primary-fanart",
            file_size=7,
        ))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        logical = db.query(Folder).one()
        mirror_folder = RepositoryFolder(
            repo_id="test",
            rel_path="mirror",
            name="mirror",
        )
        mirror_media = Media(
            repo_id="test",
            file_path="mirror/fanart.jpeg",
            file_hash="mirror-fanart",
            file_size=6,
        )
        db.add_all([mirror_folder, mirror_media])
        db.flush()
        db.add(FolderLocation(
            folder_id=logical.id,
            repository_folder_id=mirror_folder.id,
            role="MIRROR",
        ))
        db.add(RepositoryFile(
            repo_id="test",
            folder_id=mirror_folder.id,
            rel_path="mirror/fanart.jpeg",
            name="fanart.jpeg",
            mime_type="image/jpeg",
            media_type="IMAGE",
            file_size=6,
            mtime=0,
            media_id=mirror_media.id,
            materialize_status="done",
        ))
        db.commit()

        response = get_folder(logical.id, db)

        assert response.fanart_file is not None
        assert response.fanart_file.rel_path == "album/fanart.jpg"


def test_folder_list_batches_file_summary_queries(catalog_env):
    repo, session_factory = catalog_env
    for folder_name in ("alpha", "beta", "gamma"):
        directory = repo / folder_name
        directory.mkdir()
        (directory / "fanart.jpg").write_bytes(folder_name.encode())

    with session_factory() as db:
        for index, folder_name in enumerate(("alpha", "beta", "gamma")):
            db.add(Media(
                repo_id="test",
                file_path=f"{folder_name}/fanart.jpg",
                file_hash=f"batched-cover-{index}",
                file_size=len(folder_name),
            ))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        statements = []

        from sqlalchemy import event

        def record_selects(_connection, _cursor, statement, _parameters, _context, _many):
            if statement.lstrip().upper().startswith("SELECT"):
                statements.append(statement)

        event.listen(db.get_bind(), "before_cursor_execute", record_selects)
        try:
            response = list_folders(
                cursor=None, limit=20, starred=None, tag_id=None, db=db,
            )
        finally:
            event.remove(db.get_bind(), "before_cursor_execute", record_selects)

        assert len(response.items) == 3
        assert all(item.fanart_file is not None for item in response.items)
        assert len(statements) <= 8


def test_folder_list_sorts_by_release_date_with_cursor(catalog_env):
    from datetime import datetime

    repo, session_factory = catalog_env
    for folder_name in ("alpha", "beta", "gamma"):
        directory = repo / folder_name
        directory.mkdir()
        (directory / "fanart.jpg").write_bytes(folder_name.encode())

    with session_factory() as db:
        for index, folder_name in enumerate(("alpha", "beta", "gamma")):
            db.add(Media(
                repo_id="test",
                file_path=f"{folder_name}/fanart.jpg",
                file_hash=f"released-cover-{index}",
                file_size=len(folder_name),
            ))
        db.commit()

    repository_catalog.rescan("test")

    with session_factory() as db:
        # 逻辑 Folder 无 name 列;经 FolderLocation -> RepositoryFolder 取物理目录名
        link = {
            logical_id: physical_name
            for logical_id, physical_name in db.query(
                FolderLocation.folder_id, RepositoryFolder.name
            ).join(RepositoryFolder, RepositoryFolder.id == FolderLocation.repository_folder_id)
        }
        by_name = {link[folder.id]: folder for folder in db.query(Folder)}
        by_name["alpha"].released_at = datetime(2020, 1, 1)
        # beta 无发行日期 -> 兜底到其(手动调早的)created_at
        by_name["beta"].released_at = None
        by_name["beta"].created_at = datetime(2019, 6, 1)
        by_name["gamma"].released_at = datetime(2022, 5, 5)
        db.commit()

        # 默认(入库)序:id 倒序 => gamma,beta,alpha
        added = list_folders(db, limit=20)
        assert [item.name for item in added.items] == ["gamma", "beta", "alpha"]

        # released 序:gamma(2022) > alpha(2020) > beta(2019 fallback)
        released = list_folders(db, limit=20, sort="released")
        assert [item.name for item in released.items] == ["gamma", "alpha", "beta"]

        # 发行日期已透出;beta 无 release 时返回 None
        by_name_iso = {item.name: item for item in released.items}
        assert by_name_iso["gamma"].released_at == datetime(2022, 5, 5).isoformat()
        assert by_name_iso["alpha"].released_at == datetime(2020, 1, 1).isoformat()
        assert by_name_iso["beta"].released_at is None

        # 复合游标分页:每页 1 条依序翻页,无重复/遗漏
        page1 = list_folders(db, limit=1, sort="released")
        assert [item.name for item in page1.items] == ["gamma"]
        assert page1.next_cursor == f"{datetime(2022, 5, 5).isoformat()}|{by_name['gamma'].id}"
        page2 = list_folders(db, cursor=page1.next_cursor, limit=1, sort="released")
        assert [item.name for item in page2.items] == ["alpha"]
        page3 = list_folders(db, cursor=page2.next_cursor, limit=1, sort="released")
        assert [item.name for item in page3.items] == ["beta"]
        assert page3.next_cursor is None


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

        rows = _like_search(db, "album", None, None, None, None, 20)

        assert [row["id"] for row in rows] == [ordinary.id]


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


def test_folder_list_filters_and_counts_tags(catalog_env):
    repo, session_factory = catalog_env
    for name in ("alpha", "beta"):
        directory = repo / name
        directory.mkdir()
        (directory / "photo.jpg").write_bytes(b"image")
    repository_catalog.rescan("test")

    with session_factory() as db:
        tag = Tag(name="精选")
        tagged = db.query(Folder).join(FolderLocation).join(RepositoryFolder).filter(
            RepositoryFolder.rel_path == "alpha",
        ).one()
        tagged.tags.append(tag)
        db.commit()

        tags = list_folder_tags(db)
        result = list_folders(cursor=None, limit=20, starred=None, tag_id=tag.id, db=db)

        assert [(item.name, item.folder_count) for item in tags] == [("精选", 1)]
        assert [item.name for item in result.items] == ["alpha"]
        assert [item.name for item in result.items[0].tags] == ["精选"]


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

    def fake_process(db, path):
        media = Media(repo_id="test", file_path="movie.mp4", file_hash="video-hash", file_size=5)
        db.add(media)
        db.flush()
        return {"media": media, "is_new": True, "media_info": {
            "is_hdr": 1, "color_transfer": "smpte2084",
        }}

    monkeypatch.setattr(repository_materializer, "process_file", fake_process)
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

    def fake_process(db, path):
        media = Media(
            repo_id="test",
            file_path="album/movie.mp4",
            file_hash="album-video-hash",
            file_size=5,
        )
        db.add(media)
        db.flush()
        return {"media": media, "is_new": True, "media_info": {}}

    monkeypatch.setattr(repository_materializer, "process_file", fake_process)
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

    def fake_process(db, path):
        return {"media": db.query(Media).one(), "is_new": False, "media_info": {}}

    monkeypatch.setattr(repository_materializer, "process_file", fake_process)
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
