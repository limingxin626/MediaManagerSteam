"""Message read models, filters, pagination, and response assembly."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, text as sql_text
from sqlalchemy.orm import Session

from app.models import Message, MessageMedia, message_tag, media_tag
from app.modules.message.schemas import (
    MEDIA_PREVIEW_LIMIT,
    MessageDetailResponse,
    MessageFolderItem,
    MessageMediaItem,
    MessageDateCount,
    MessageDatesResponse,
    MessageResponse,
    CursorResponse,
    MessageSearchCursorResponse,
    MessageSearchItem,
    MessageSyncMediaItem,
    MessageSyncResponse,
    MessageTagItem,
)


def aggregate_tags(msg: Message) -> list[MessageTagItem]:
    tag_map = {tag.id: tag for tag in msg.tags}
    for relation in msg.message_media:
        if relation.media:
            for tag in relation.media.tags:
                tag_map.setdefault(tag.id, tag)
    return [
        MessageTagItem(id=tag.id, name=tag.name, category=tag.category)
        for tag in tag_map.values()
    ]


def aggregate_tags_raw(msg: Message) -> list:
    tag_map = {tag.id: tag for tag in msg.tags}
    for relation in msg.message_media:
        if relation.media:
            for tag in relation.media.tags:
                tag_map.setdefault(tag.id, tag)
    return list(tag_map.values())


def folder_fields(msg: Message) -> dict:
    primary = next((link.folder for link in msg.folder_links if link.role == "PRIMARY"), None)
    return {
        "folder_count": len(msg.folder_links),
        "primary_repo_id": primary.repo_id if primary else None,
        "primary_folder_path": primary.rel_path if primary else None,
    }


def folder_items(msg: Message) -> list[MessageFolderItem]:
    return [
        MessageFolderItem(
            id=link.folder.id, repo_id=link.folder.repo_id,
            rel_path=link.folder.rel_path, name=link.folder.name, role=link.role,
        )
        for link in sorted(msg.folder_links, key=lambda item: (item.role != "PRIMARY", item.folder.id))
    ]


def parse_cursor(cursor: Optional[str]) -> Optional[datetime]:
    if not cursor:
        return None
    try:
        return datetime.fromisoformat(cursor)
    except ValueError as exc:
        raise ValueError("Invalid cursor format") from exc


def build_detail_query(
    db: Session, collection_id: Optional[int], query_text: Optional[str],
    media_id: Optional[int], tag_id: Optional[int], starred: Optional[bool] = None,
    issue_id: Optional[int] = None,
):
    query = db.query(Message).filter(~Message.folder_links.any())
    if collection_id is not None:
        query = query.filter(
            Message.collection_id.is_(None) if collection_id == 0
            else Message.collection_id == collection_id
        )
    if issue_id is not None:
        query = query.filter(
            Message.issue_id.is_(None) if issue_id == 0 else Message.issue_id == issue_id
        )
    if query_text:
        query = query.filter(Message.text.ilike(f"%{query_text}%"))
    if media_id:
        query = query.join(MessageMedia).filter(MessageMedia.media_id == media_id)
    if tag_id:
        message_ids = db.query(message_tag.c.message_id).filter(message_tag.c.tag_id == tag_id)
        media_message_ids = (
            db.query(MessageMedia.message_id)
            .join(media_tag, MessageMedia.media_id == media_tag.c.media_id)
            .filter(media_tag.c.tag_id == tag_id)
        )
        query = query.filter(Message.id.in_(message_ids.union(media_message_ids)))
    if starred is not None:
        query = query.filter(Message.starred == (1 if starred else 0))
    return query


def build_message_query(
    db: Session, collection_id: Optional[int], query_text: Optional[str],
    media_id: Optional[int], tag_id: Optional[int], cursor_time: Optional[datetime],
    starred: Optional[bool] = None, inclusive: bool = False, issue_id: Optional[int] = None,
):
    query = build_detail_query(
        db, collection_id, query_text, media_id, tag_id, starred, issue_id
    )
    if cursor_time:
        query = query.filter(
            Message.created_at <= cursor_time if inclusive else Message.created_at < cursor_time
        )
    return query.order_by(Message.created_at.desc())


def paginate(query, limit: int):
    rows = query.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = items[-1].created_at.isoformat() if has_more and items else None
    return items, has_more, next_cursor


def media_items_for(
    db: Session, message_id: int, limit: Optional[int] = MEDIA_PREVIEW_LIMIT
) -> List[MessageMediaItem]:
    query = (
        db.query(MessageMedia).filter(MessageMedia.message_id == message_id)
        .order_by(MessageMedia.position)
    )
    if limit is not None:
        query = query.limit(limit)
    return [MessageMediaItem.model_validate(row.media) for row in query.all() if row.media]


def batch_media_items(
    db: Session, message_ids: List[int], limit: Optional[int] = MEDIA_PREVIEW_LIMIT
) -> dict:
    rows = (
        db.query(MessageMedia).filter(MessageMedia.message_id.in_(message_ids))
        .order_by(MessageMedia.message_id, MessageMedia.position).all()
    )
    grouped: dict[int, List[MessageMediaItem]] = {}
    per_message: dict[int, int] = {}
    for row in rows:
        if not row.media:
            continue
        count = per_message.get(row.message_id, 0)
        if limit is not None and count >= limit:
            continue
        per_message[row.message_id] = count + 1
        grouped.setdefault(row.message_id, []).append(MessageMediaItem.model_validate(row.media))
    return grouped


def build_detail_response(
    db: Session, msg: Message, media_limit: Optional[int] = MEDIA_PREVIEW_LIMIT,
    media_by_msg: Optional[dict] = None,
) -> MessageDetailResponse:
    media_items = (
        media_by_msg.get(msg.id, []) if media_by_msg is not None
        else media_items_for(db, msg.id, limit=media_limit)
    )
    return MessageDetailResponse(
        id=msg.id, text=msg.text, collection_id=msg.collection_id,
        collection_name=msg.collection.name if msg.collection else None,
        issue_id=msg.issue_id, issue_title=msg.issue.title if msg.issue else None,
        media_count=len(media_items), starred=bool(msg.starred), media_items=media_items,
        tags=aggregate_tags(msg), folders=folder_items(msg),
        created_at=msg.created_at.isoformat(), updated_at=msg.updated_at.isoformat(),
        **folder_fields(msg),
    )


def sync_media_item(relation) -> MessageSyncMediaItem:
    item = MessageSyncMediaItem.model_validate(relation.media)
    item.position = relation.position
    return item


def build_sync_response(db: Session, message: Message) -> MessageSyncResponse:
    relations = (
        db.query(MessageMedia).filter(MessageMedia.message_id == message.id)
        .order_by(MessageMedia.position).all()
    )
    media_items = [sync_media_item(row) for row in relations if row.media]
    return MessageSyncResponse(
        id=message.id, text=message.text, collection_id=message.collection_id,
        collection_name=message.collection.name if message.collection else None,
        issue_id=message.issue_id, issue_title=message.issue.title if message.issue else None,
        starred=bool(message.starred), created_at=message.created_at.isoformat(),
        updated_at=message.updated_at.isoformat(), media_items=media_items,
        media_count=len(media_items), tags=aggregate_tags(message), **folder_fields(message),
    )


def _search_where(params, collection_id, issue_id, tag_id, starred):
    where = ["NOT EXISTS (SELECT 1 FROM message_folder mf WHERE mf.message_id = m.id)"]
    for column, value in (("collection_id", collection_id), ("issue_id", issue_id)):
        if value is not None:
            if value == 0:
                where.append(f"m.{column} IS NULL")
            else:
                where.append(f"m.{column} = :{column}")
                params[column] = value
    if starred is not None:
        where.append("m.starred = :starred")
        params["starred"] = 1 if starred else 0
    if tag_id is not None:
        where.append("(m.id IN (SELECT message_id FROM message_tag WHERE tag_id = :tag_id) OR m.id IN (SELECT mm.message_id FROM message_media mm JOIN media_tag mt ON mt.media_id = mm.media_id WHERE mt.tag_id = :tag_id))")
        params["tag_id"] = tag_id
    return where


def _like_search(db, query, collection_id, issue_id, tag_id, starred, limit):
    params = {"pat": f"%{query}%", "limit": limit + 1}
    where = ["m.text LIKE :pat", *_search_where(params, collection_id, issue_id, tag_id, starred)]
    raw = db.execute(sql_text(f"SELECT m.id, m.created_at, m.collection_id, m.issue_id, m.starred, 0.0 AS rank, m.text FROM message m WHERE {' AND '.join(where)} ORDER BY m.created_at DESC LIMIT :limit"), params).fetchall()

    def snippet(value):
        value = value or ""
        index = value.lower().find(query.lower())
        if index < 0:
            return value[:120] + ("…" if len(value) > 120 else "")
        start, end = max(0, index - 30), min(len(value), index + len(query) + 30)
        return ("…" if start else "") + value[start:index] + "«" + value[index:index + len(query)] + "»" + value[index + len(query):end] + ("…" if end < len(value) else "")

    return [{"id": row.id, "collection_id": row.collection_id, "issue_id": row.issue_id, "starred": row.starred, "rank": row.rank, "snippet": snippet(row.text)} for row in raw]


def search(db: Session, *, query: str, collection_id=None, issue_id=None, tag_id=None, starred=None, limit=20, cursor=None) -> MessageSearchCursorResponse:
    tokens = [token for token in query.replace('"', " ").split() if token]
    if not tokens:
        return MessageSearchCursorResponse(items=[], next_cursor=None, has_more=False)
    match_query = " ".join(f'"{token}"' for token in tokens)
    params = {"q": match_query, "limit": limit + 1}
    where = ["message_fts MATCH :q", *_search_where(params, collection_id, issue_id, tag_id, starred)]
    if cursor:
        try:
            rank, item_id = cursor.split("|", 1)
            params.update(c_rank=float(rank), c_id=int(item_id))
        except (ValueError, AttributeError) as exc:
            raise ValueError("Invalid cursor format") from exc
        where.append("(bm25(message_fts) > :c_rank OR (bm25(message_fts) = :c_rank AND m.id < :c_id))")
    sql = f"SELECT m.id, m.collection_id, m.issue_id, m.starred, bm25(message_fts) AS rank, snippet(message_fts, 0, '«', '»', '…', 16) AS snippet FROM message_fts JOIN message m ON m.id = message_fts.rowid WHERE {' AND '.join(where)} ORDER BY bm25(message_fts), m.id DESC LIMIT :limit"
    rows = [dict(row._mapping) for row in db.execute(sql_text(sql), params).fetchall()]
    fallback = False
    if not rows and cursor is None:
        fallback_query = "".join(tokens)
        rows = _like_search(db, fallback_query, collection_id, issue_id, tag_id, starred, limit) if fallback_query else []
        fallback = bool(rows)
    has_more = len(rows) > limit
    rows = rows[:limit]
    ids = [row["id"] for row in rows]
    messages = {item.id: item for item in db.query(Message).filter(Message.id.in_(ids)).all()}
    counts = dict(db.query(MessageMedia.message_id, func.count(MessageMedia.media_id)).filter(MessageMedia.message_id.in_(ids)).group_by(MessageMedia.message_id).all()) if ids else {}
    items = []
    for row in rows:
        message = messages.get(row["id"])
        if message:
            items.append(MessageSearchItem(id=message.id, created_at=message.created_at.isoformat(), snippet=row["snippet"] or "", collection_id=row["collection_id"], collection_name=message.collection.name if message.collection else None, issue_id=row["issue_id"], issue_title=message.issue.title if message.issue else None, tags=[tag.name for tag in aggregate_tags_raw(message)], media_count=counts.get(message.id, 0), starred=bool(row["starred"])))
    next_cursor = f"{rows[-1]['rank']}|{rows[-1]['id']}" if has_more and rows and not fallback else None
    return MessageSearchCursorResponse(items=items, next_cursor=next_cursor, has_more=has_more and not fallback)


def get_detail(db: Session, message_id: int) -> MessageDetailResponse:
    message = db.query(Message).filter(Message.id == message_id, ~Message.folder_links.any()).first()
    if message is None:
        raise LookupError("Message not found")
    return build_detail_response(db, message, media_limit=None)


def get_detail_after_write(db: Session, message_id: int) -> MessageDetailResponse:
    message = db.get(Message, message_id)
    if message is None:
        raise LookupError("Message not found")
    db.refresh(message)
    return build_detail_response(db, message, media_limit=None)


def sync_all(db: Session) -> list[MessageSyncResponse]:
    messages = db.query(Message).filter(~Message.folder_links.any()).order_by(Message.created_at.desc()).all()
    if not messages:
        return []
    ids = [message.id for message in messages]
    relations = db.query(MessageMedia).filter(MessageMedia.message_id.in_(ids)).order_by(MessageMedia.message_id, MessageMedia.position).all()
    by_message: dict[int, list] = {}
    for relation in relations:
        by_message.setdefault(relation.message_id, []).append(relation)
    results = []
    for message in messages:
        media_items = [sync_media_item(row) for row in by_message.get(message.id, []) if row.media]
        results.append(MessageSyncResponse(id=message.id, text=message.text, collection_id=message.collection_id, collection_name=message.collection.name if message.collection else None, media_count=len(media_items), issue_id=message.issue_id, issue_title=message.issue.title if message.issue else None, starred=bool(message.starred), created_at=message.created_at.isoformat(), updated_at=message.updated_at.isoformat(), media_items=media_items, tags=aggregate_tags(message), **folder_fields(message)))
    return results


def list_messages(db: Session, *, cursor=None, limit=20, collection_id=None, issue_id=None, starred=None) -> CursorResponse:
    query = build_message_query(db, collection_id, None, None, None, parse_cursor(cursor), starred=starred, issue_id=issue_id)
    items, has_more, next_cursor = paginate(query, limit)
    ids = [message.id for message in items]
    counts = dict(db.query(MessageMedia.message_id, func.count()).filter(MessageMedia.message_id.in_(ids)).group_by(MessageMedia.message_id).all()) if ids else {}
    result = [MessageResponse(id=message.id, text=message.text, collection_id=message.collection_id, collection_name=message.collection.name if message.collection else None, issue_id=message.issue_id, issue_title=message.issue.title if message.issue else None, media_count=counts.get(message.id, 0), starred=bool(message.starred), created_at=message.created_at.isoformat(), updated_at=message.updated_at.isoformat(), **folder_fields(message)) for message in items]
    return CursorResponse(items=result, next_cursor=next_cursor, has_more=has_more)


def message_dates(db: Session, *, year, month, collection_id=None, issue_id=None, query_text=None, media_id=None, tag_id=None) -> MessageDatesResponse:
    date_label = func.strftime("%Y-%m-%d", Message.created_at).label("date_str")
    query = db.query(date_label, func.count().label("cnt")).filter(~Message.folder_links.any())
    for column, value in ((Message.collection_id, collection_id), (Message.issue_id, issue_id)):
        if value is not None:
            query = query.filter(column.is_(None) if value == 0 else column == value)
    if query_text:
        query = query.filter(Message.text.ilike(f"%{query_text}%"))
    if media_id:
        query = query.join(MessageMedia, Message.id == MessageMedia.message_id).filter(MessageMedia.media_id == media_id)
    if tag_id:
        direct = db.query(message_tag.c.message_id).filter(message_tag.c.tag_id == tag_id)
        through_media = db.query(MessageMedia.message_id).join(media_tag, MessageMedia.media_id == media_tag.c.media_id).filter(media_tag.c.tag_id == tag_id)
        query = query.filter(Message.id.in_(direct.union(through_media)))
    rows = query.filter(func.strftime("%Y", Message.created_at) == str(year), func.strftime("%m", Message.created_at) == str(month).zfill(2)).group_by(date_label).all()
    return MessageDatesResponse(dates=[MessageDateCount(date=row.date_str, count=row.cnt) for row in rows])
