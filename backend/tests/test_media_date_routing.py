from datetime import datetime

from app.models import Media
from app.models.repository_catalog import RepositoryFile, RepositoryFolder
from app.modules.media.router import get_media, get_media_timeline


def add_media(
    db,
    media_id,
    *,
    taken_at=None,
    file_created_at=None,
    created_at=None,
    file_path=None,
    mime_type="image/jpeg",
    video_media_id=None,
):
    media = Media(
        id=media_id,
        repo_id="test",
        file_path=file_path or f"{media_id}.jpg",
        file_hash=f"hash-{media_id}",
        file_size=1,
        mime_type=mime_type,
        video_media_id=video_media_id,
        taken_at=taken_at,
        file_created_at=file_created_at,
        created_at=created_at or datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    db.add(media)
    db.flush()
    return media


def list_media(db, **kwargs):
    return get_media(
        cursor=kwargs.get("cursor"),
        direction=kwargs.get("direction"),
        limit=kwargs.get("limit", 20),
        message_id=None,
        message_ids=None,
        starred=None,
        type=kwargs.get("type"),
        tag_id=None,
        collection_id=None,
        has_physical_file=kwargs.get("has_physical_file"),
        db=db,
    )


def test_media_sort_uses_taken_then_file_created_and_ignores_db_created(catalog_env):
    _, session_factory = catalog_env
    with session_factory() as db:
        add_media(
            db,
            1,
            taken_at=datetime(2024, 1, 1),
            file_created_at=datetime(2025, 1, 1),
            created_at=datetime(2030, 1, 1),
        )
        add_media(db, 2, file_created_at=datetime(2023, 1, 1), created_at=datetime(2040, 1, 1))
        add_media(db, 3, created_at=datetime(2050, 1, 1))
        db.commit()

        result = list_media(db)
        assert [item.id for item in result.items] == [1, 2, 3]


def test_media_same_time_paginates_by_id_and_undated_uses_stable_cursor(catalog_env):
    _, session_factory = catalog_env
    same_time = datetime(2024, 1, 1)
    with session_factory() as db:
        add_media(db, 1, file_created_at=same_time)
        add_media(db, 2, file_created_at=same_time)
        add_media(db, 3)
        db.commit()

        first = list_media(db, limit=1)
        second = list_media(db, limit=1, cursor=first.next_cursor)
        third = list_media(db, limit=1, cursor=second.next_cursor)

        assert [first.items[0].id, second.items[0].id, third.items[0].id] == [2, 1, 3]
        assert second.next_cursor == f"{same_time.isoformat()}|1"


def test_media_filters_by_completed_physical_file(catalog_env):
    _, session_factory = catalog_env
    with session_factory() as db:
        folder = RepositoryFolder(repo_id="test", rel_path="", name="test")
        db.add(folder)
        db.flush()
        add_media(db, 1, file_created_at=datetime(2024, 1, 1))
        add_media(db, 2, file_created_at=datetime(2024, 1, 2))
        add_media(db, 3, file_created_at=datetime(2024, 1, 3))
        db.add_all([
            RepositoryFile(
                repo_id="test", folder_id=folder.id, rel_path="1-a.jpg", name="1-a.jpg",
                media_type="image", file_size=1, mtime=1, media_id=1, materialize_status="done",
            ),
            RepositoryFile(
                repo_id="test", folder_id=folder.id, rel_path="1-b.jpg", name="1-b.jpg",
                media_type="image", file_size=1, mtime=1, media_id=1, materialize_status="done",
            ),
            RepositoryFile(
                repo_id="test", folder_id=folder.id, rel_path="2.jpg", name="2.jpg",
                media_type="image", file_size=1, mtime=1, media_id=2, materialize_status="pending",
            ),
        ])
        db.commit()

        existing = list_media(db, has_physical_file=True)
        missing = list_media(db, has_physical_file=False)
        all_media = list_media(db)

        assert [item.id for item in existing.items] == [1]
        assert [item.id for item in missing.items] == [3, 2]
        assert [item.id for item in all_media.items] == [3, 2, 1]


def test_timeline_uses_file_created_fallback_and_excludes_undated(catalog_env):
    _, session_factory = catalog_env
    with session_factory() as db:
        add_media(db, 1, taken_at=datetime(2024, 2, 3), file_created_at=datetime(2023, 1, 1))
        add_media(db, 2, file_created_at=datetime(2023, 1, 1))
        add_media(db, 3)
        db.commit()

        rows = get_media_timeline(
            starred=None,
            type=None,
            tag_id=None,
            collection_id=None,
            has_physical_file=None,
            db=db,
        )
        assert [(row.year, row.month, row.day, row.count) for row in rows] == [
            (2024, 2, 3, 1),
            (2023, 1, 1, 1),
        ]


def test_screenshot_filter_includes_gifs_and_video_preview_media(catalog_env):
    _, session_factory = catalog_env
    media_time = datetime(2024, 2, 3)
    with session_factory() as db:
        add_media(db, 1, file_created_at=media_time, mime_type="video/mp4")
        add_media(db, 2, file_created_at=media_time, file_path="animated.GIF", mime_type="image/gif")
        add_media(db, 3, file_created_at=media_time, video_media_id=1)
        add_media(db, 4, file_created_at=media_time)
        db.commit()

        result = list_media(db, type="screenshot")
        timeline = get_media_timeline(
            starred=None,
            type="screenshot",
            tag_id=None,
            collection_id=None,
            has_physical_file=None,
            db=db,
        )

        assert {item.id for item in result.items} == {2, 3}
        assert [(row.year, row.month, row.day, row.count) for row in timeline] == [
            (2024, 2, 3, 2),
        ]


def add_repository_file(db, folder, file_id, media_id, *, status="done"):
    db.add(RepositoryFile(
        id=file_id,
        repo_id="test",
        folder_id=folder.id,
        rel_path=f"physical-{file_id}.jpg",
        name=f"physical-{file_id}.jpg",
        media_type="image",
        file_size=1,
        mtime=1,
        media_id=media_id,
        materialize_status=status,
    ))
    db.flush()


def test_physical_file_filter_uses_completed_catalog_links_without_duplicates(catalog_env):
    _, session_factory = catalog_env
    media_time = datetime(2024, 2, 3)
    with session_factory() as db:
        folder = RepositoryFolder(repo_id="test", rel_path="", name="test")
        db.add(folder)
        db.flush()
        add_media(db, 1, file_created_at=media_time)
        add_media(db, 2, file_created_at=media_time)
        add_media(db, 3, file_created_at=media_time)
        add_repository_file(db, folder, 1, 1)
        add_repository_file(db, folder, 2, 1)
        add_repository_file(db, folder, 3, 2, status="pending")
        db.commit()

        all_items = list_media(db)
        existing = list_media(db, has_physical_file=True)
        missing = list_media(db, has_physical_file=False)

        assert {item.id for item in all_items.items} == {1, 2, 3}
        assert [item.id for item in existing.items] == [1]
        assert {item.id for item in missing.items} == {2, 3}

        existing_timeline = get_media_timeline(
            starred=None,
            type=None,
            tag_id=None,
            collection_id=None,
            has_physical_file=True,
            db=db,
        )
        missing_timeline = get_media_timeline(
            starred=None,
            type=None,
            tag_id=None,
            collection_id=None,
            has_physical_file=False,
            db=db,
        )
        assert [(row.year, row.month, row.day, row.count) for row in existing_timeline] == [
            (2024, 2, 3, 1),
        ]
        assert [(row.year, row.month, row.day, row.count) for row in missing_timeline] == [
            (2024, 2, 3, 2),
        ]
