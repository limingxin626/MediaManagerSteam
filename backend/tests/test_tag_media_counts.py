from datetime import datetime

from app.models import Media, Message, MessageMedia, Tag
from app.modules.media.router import get_media, get_media_timeline
from app.modules.tag.router import get_tags


def add_media(db, media_id, *, file_created_at=None, video_media_id=None):
    media = Media(
        id=media_id,
        repo_id="test",
        file_path=f"{media_id}.jpg",
        file_hash=f"hash-{media_id}",
        file_size=1,
        mime_type="image/jpeg",
        file_created_at=file_created_at,
        video_media_id=video_media_id,
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    db.add(media)
    db.flush()
    return media


def test_media_page_tags_use_direct_media_tags_only(catalog_env):
    _, session_factory = catalog_env
    with session_factory() as db:
        tag = Tag(name="测试")
        message = Message(text="tagged message", tags=[tag])
        inherited = add_media(db, 1, file_created_at=datetime(2024, 1, 1))
        visible = add_media(db, 2, file_created_at=datetime(2024, 1, 1))
        undated = add_media(db, 3)
        preview = add_media(db, 4, file_created_at=datetime(2024, 1, 1), video_media_id=visible.id)
        visible.tags.append(tag)
        undated.tags.append(tag)
        preview.tags.append(tag)
        db.add(MessageMedia(message=message, media=inherited, position=0))
        db.commit()

        tags = get_tags(name=None, has_media=True, db=db)
        media = get_media(
            cursor=None,
            direction=None,
            limit=20,
            message_id=None,
            message_ids=None,
            starred=None,
            type=None,
            tag_id=tag.id,
            collection_id=None,
            has_physical_file=None,
            db=db,
        )
        timeline = get_media_timeline(
            starred=None,
            type=None,
            tag_id=tag.id,
            collection_id=None,
            has_physical_file=None,
            db=db,
        )

        assert [(item.id, item.message_count) for item in tags] == [(tag.id, 1)]
        assert {item.id for item in media.items} == {visible.id, undated.id}
        assert sum(item.count for item in timeline) == 1
