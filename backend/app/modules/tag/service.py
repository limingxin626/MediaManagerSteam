"""Tag queries and mutation use cases."""
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import Media, Tag, media_tag, message_tag
from app.modules.tag.schemas import TagResponse
from app.shared.unit_of_work import commit


def _response(tag: Tag, count: int) -> TagResponse:
    return TagResponse(id=tag.id, name=tag.name, category=tag.category, message_count=count)


def list_tags(db: Session, name: str | None, has_media: bool) -> list[TagResponse]:
    media_counts = db.query(media_tag.c.tag_id, func.count().label("cnt"))
    if has_media:
        media_counts = media_counts.join(Media, Media.id == media_tag.c.media_id).filter(Media.video_media_id.is_(None), func.coalesce(Media.taken_at, Media.file_created_at).is_not(None))
    media_counts = media_counts.group_by(media_tag.c.tag_id).subquery()
    if has_media:
        total = func.coalesce(media_counts.c.cnt, 0)
        query = db.query(Tag, total).outerjoin(media_counts, Tag.id == media_counts.c.tag_id).filter(total > 0)
    else:
        message_counts = db.query(message_tag.c.tag_id, func.count().label("cnt")).group_by(message_tag.c.tag_id).subquery()
        total = func.coalesce(message_counts.c.cnt, 0) + func.coalesce(media_counts.c.cnt, 0)
        query = db.query(Tag, total).outerjoin(message_counts, Tag.id == message_counts.c.tag_id).outerjoin(media_counts, Tag.id == media_counts.c.tag_id)
    if name: query = query.filter(Tag.name.ilike(f"%{name}%"))
    return [_response(tag, count) for tag, count in query.order_by(total.desc()).all()]


def create(db: Session, name: str, category: str | None) -> TagResponse:
    if db.query(Tag).filter(Tag.name == name).first(): raise FileExistsError("标签名已存在")
    tag = Tag(name=name, category=category); db.add(tag); commit(db); db.refresh(tag)
    return _response(tag, 0)


def update(db: Session, tag_id: int, name: str | None, category: str | None, fields_set: set[str]) -> TagResponse:
    tag = db.get(Tag, tag_id)
    if tag is None: raise LookupError("Tag not found")
    if name is not None and db.query(Tag).filter(Tag.name == name, Tag.id != tag_id).first(): raise FileExistsError("标签名已存在")
    if "name" in fields_set: tag.name = name
    if "category" in fields_set: tag.category = category
    commit(db); db.refresh(tag)
    count = db.query(func.count()).select_from(message_tag).filter(message_tag.c.tag_id == tag.id).scalar() or 0
    return _response(tag, count)


def delete(db: Session, tag_id: int) -> None:
    tag = db.get(Tag, tag_id)
    if tag is None: raise LookupError("Tag not found")
    db.execute(message_tag.delete().where(message_tag.c.tag_id == tag_id)); db.execute(media_tag.delete().where(media_tag.c.tag_id == tag_id)); db.delete(tag); commit(db)
