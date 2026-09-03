"""Reusable media filters and cursor encoding."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Integer, exists, func, or_

from app.models import Media, Message, MessageMedia, media_tag, message_tag
from app.modules.media.schemas import MediaCursorResponse, MediaDetailResponse, MediaResponse, TimelineItem, VideoPreviewItem
from app.models.repository_catalog import RepositoryFile

MEDIA_TIME_SENTINEL = datetime.min


def media_cursor(item: Media) -> str:
    media_time = item.taken_at or item.file_created_at or MEDIA_TIME_SENTINEL
    return f"{media_time.isoformat()}|{item.id}"


def filter_physical_file(query, has_physical_file: Optional[bool]):
    if has_physical_file is None:
        return query
    linked = exists().where(
        RepositoryFile.media_id == Media.id, RepositoryFile.materialize_status == "done"
    )
    return query.filter(linked if has_physical_file else ~linked)


def filter_media_type(query, media_type: Optional[str]):
    if media_type == "screenshot":
        return query.filter(or_(
            func.lower(Media.mime_type) == "image/gif",
            func.lower(Media.file_path).like("%.gif"),
            Media.video_media_id.is_not(None),
        ))
    query = query.filter(Media.video_media_id.is_(None))
    if media_type == "video":
        return query.filter(Media.mime_type.like("video/%"))
    if media_type == "image":
        return query.filter(Media.mime_type.like("image/%"))
    return query


def _apply_filters(db, query, *, media_type=None, starred=None, tag_id=None, collection_id=None, message_ids=None, has_physical_file=None):
    query = filter_media_type(query, media_type)
    query = filter_physical_file(query, has_physical_file)
    if starred is not None:
        query = query.filter(Media.starred == (1 if starred else 0))
    if message_ids:
        query = query.filter(Media.id.in_(db.query(MessageMedia.media_id).filter(MessageMedia.message_id.in_(message_ids))))
    if tag_id is not None:
        query = query.filter(Media.id.in_(db.query(media_tag.c.media_id).filter(media_tag.c.tag_id == tag_id)))
    if collection_id is not None:
        query = query.filter(Media.id.in_(db.query(MessageMedia.media_id).join(Message).filter(Message.collection_id == collection_id)))
    return query


def list_media(db, *, cursor=None, direction=None, limit=20, message_id=None, message_ids=None, starred=None, media_type=None, tag_id=None, collection_id=None, has_physical_file=None) -> MediaCursorResponse:
    if message_id:
        ids = [row.media_id for row in db.query(MessageMedia).filter_by(message_id=message_id).order_by(MessageMedia.position).all()]
        rows = filter_physical_file(db.query(Media).filter(Media.id.in_(ids)), has_physical_file).all()
        by_id = {row.id: row for row in rows}
        return MediaCursorResponse(items=[MediaResponse.model_validate(by_id[mid]) for mid in ids if mid in by_id], next_cursor=None, has_more=False)
    query = _apply_filters(db, db.query(Media), media_type=media_type, starred=starred, tag_id=tag_id, collection_id=collection_id, message_ids=message_ids, has_physical_file=has_physical_file)
    media_time = func.coalesce(Media.taken_at, Media.file_created_at, MEDIA_TIME_SENTINEL)
    if cursor:
        try:
            raw_time, raw_id = cursor.rsplit("|", 1)
            cursor_time, cursor_id = datetime.fromisoformat(raw_time), int(raw_id)
        except (ValueError, IndexError) as exc:
            raise ValueError("Invalid cursor format") from exc
        if direction == "around":
            half = limit // 2
            before = query.filter((media_time > cursor_time) | ((media_time == cursor_time) & (Media.id >= cursor_id))).order_by(media_time.asc(), Media.id.asc()).limit(half + 1).all()
            after = query.filter((media_time < cursor_time) | ((media_time == cursor_time) & (Media.id < cursor_id))).order_by(media_time.desc(), Media.id.desc()).limit(limit - half + 1).all()
            has_before, has_more = len(before) > half, len(after) > limit - half
            items = list(reversed(before[:half])) + after[:limit - half]
            return MediaCursorResponse(items=[MediaResponse.model_validate(row) for row in items], next_cursor=media_cursor(items[-1]) if has_more and items else None, prev_cursor=media_cursor(items[0]) if has_before and items else None, has_more=has_more, has_more_before=has_before)
        if direction == "forward":
            query = query.filter((media_time > cursor_time) | ((media_time == cursor_time) & (Media.id > cursor_id))).order_by(media_time.asc(), Media.id.asc())
        else:
            query = query.filter((media_time < cursor_time) | ((media_time == cursor_time) & (Media.id < cursor_id))).order_by(media_time.desc(), Media.id.desc())
    else:
        query = query.order_by(media_time.desc(), Media.id.desc())
    rows = query.limit(limit + 1).all()
    items, has_more = rows[:limit], len(rows) > limit
    return MediaCursorResponse(items=[MediaResponse.model_validate(row) for row in items], next_cursor=media_cursor(items[-1]) if has_more and items else None, prev_cursor=None, has_more=has_more, has_more_before=False)


def timeline(db, *, starred=None, media_type=None, tag_id=None, collection_id=None, has_physical_file=None) -> list[TimelineItem]:
    media_time = func.coalesce(Media.taken_at, Media.file_created_at)
    year = func.cast(func.strftime("%Y", media_time), Integer)
    month = func.cast(func.strftime("%m", media_time), Integer)
    day = func.cast(func.strftime("%d", media_time), Integer)
    query = db.query(year.label("year"), month.label("month"), day.label("day"), func.count().label("count")).filter(media_time.is_not(None))
    query = _apply_filters(db, query, media_type=media_type, starred=starred, tag_id=tag_id, collection_id=collection_id, has_physical_file=has_physical_file)
    rows = query.group_by("year", "month", "day").order_by(year.desc(), month.desc(), day.desc()).all()
    return [TimelineItem(year=row.year, month=row.month, day=row.day, count=row.count) for row in rows]


def feed(db, *, cursor=None, limit=40, tag_id=None, collection_id=None, starred=None) -> MediaCursorResponse:
    query = db.query(Media, MessageMedia).join(MessageMedia, MessageMedia.media_id == Media.id).join(Message, Message.id == MessageMedia.message_id)
    if tag_id is not None:
        message_ids = db.query(message_tag.c.message_id.label("message_id")).filter(message_tag.c.tag_id == tag_id)
        media_message_ids = db.query(MessageMedia.message_id.label("message_id")).join(media_tag, MessageMedia.media_id == media_tag.c.media_id).filter(media_tag.c.tag_id == tag_id)
        combined = message_ids.union(media_message_ids).subquery()
        query = query.filter(Message.id.in_(db.query(combined.c.message_id)))
    if collection_id is not None:
        query = query.filter(Message.collection_id == collection_id)
    if starred is not None:
        query = query.filter(Media.starred == (1 if starred else 0))
    if cursor is not None:
        query = query.filter(MessageMedia.id < cursor)
    rows = query.order_by(MessageMedia.id.desc()).limit(limit + 1).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = []
    for media, relation in rows:
        item = MediaResponse.model_validate(media)
        item.source_message_id = relation.message_id
        items.append(item)
    return MediaCursorResponse(items=items, next_cursor=str(rows[-1][1].id) if has_more and rows else None, has_more=has_more)


def detail(db, media_id: int) -> MediaDetailResponse:
    media = db.get(Media, media_id)
    if media is None: raise LookupError("Media not found")
    ids = [item for (item,) in db.query(MessageMedia.message_id).filter(MessageMedia.media_id == media_id).distinct().all()]
    data = MediaResponse.model_validate(media).model_dump(); data["messages"] = [{"id": item} for item in ids]
    return MediaDetailResponse(**data)


def require_video(db, media_id: int) -> Media:
    media = db.get(Media, media_id)
    if media is None: raise LookupError("Media not found")
    if not (media.mime_type or "").startswith("video/"): raise ValueError("Target media is not a video")
    return media


def previews(db, media_id: int) -> list[VideoPreviewItem]:
    require_video(db, media_id)
    rows = db.query(Media).filter(Media.video_media_id == media_id).order_by(Media.frame_ms.asc()).all()
    return [VideoPreviewItem.model_validate(row) for row in rows]
