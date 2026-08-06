from datetime import datetime

from app.models import Media
from app.routers.media import get_media, get_media_timeline


def add_media(db, media_id, *, taken_at=None, file_created_at=None, created_at=None):
    media = Media(
        id=media_id,
        repo_id="test",
        file_path=f"{media_id}.jpg",
        file_hash=f"hash-{media_id}",
        file_size=1,
        mime_type="image/jpeg",
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
        type=None,
        tag_id=None,
        collection_id=None,
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


def test_timeline_uses_file_created_fallback_and_excludes_undated(catalog_env):
    _, session_factory = catalog_env
    with session_factory() as db:
        add_media(db, 1, taken_at=datetime(2024, 2, 3), file_created_at=datetime(2023, 1, 1))
        add_media(db, 2, file_created_at=datetime(2023, 1, 1))
        add_media(db, 3)
        db.commit()

        rows = get_media_timeline(starred=None, type=None, tag_id=None, collection_id=None, db=db)
        assert [(row.year, row.month, row.day, row.count) for row in rows] == [
            (2024, 2, 3, 1),
            (2023, 1, 1, 1),
        ]
