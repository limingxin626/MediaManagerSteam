"""Collection queries and mutation use cases."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import config
from app.models import Collection, Message
from app.modules.collection.schemas import CollectionListResponse, CollectionResponse, CollectionSyncResponse
from app.shared.unit_of_work import commit


def _response(collection: Collection, message_count: int) -> CollectionResponse:
    return CollectionResponse(id=collection.id, name=collection.name, description=collection.description, cover_path=collection.cover_path, message_count=message_count, created_at=collection.created_at.isoformat(), updated_at=collection.updated_at.isoformat())


def sync(db: Session) -> list[CollectionSyncResponse]:
    return [CollectionSyncResponse(id=item.id, name=item.name, description=item.description, cover=config.get_collection_cover_url(item.id) if item.cover_path else None) for item in db.query(Collection).order_by(Collection.name).all()]


def list_collections(db: Session, name: str | None) -> CollectionListResponse:
    query = db.query(Collection)
    if name:
        query = query.filter(Collection.name.ilike(f"%{name}%"))
    collections = query.all()
    no_collection_count = db.query(func.count(Message.id)).filter(Message.collection_id.is_(None)).scalar() or 0
    ids = [item.id for item in collections]
    counts = {} if not ids else dict(db.query(Message.collection_id, func.count(Message.id)).filter(Message.collection_id.in_(ids)).group_by(Message.collection_id).all())
    items = [_response(item, counts.get(item.id, 0)) for item in collections if counts.get(item.id, 0) > 0]
    items.sort(key=lambda item: item.message_count, reverse=True)
    return CollectionListResponse(items=items, no_collection_count=no_collection_count)


def create(db: Session, name: str, description: str | None) -> CollectionResponse:
    if db.query(Collection).filter(Collection.name == name).first():
        raise FileExistsError("合集名已存在")
    item = Collection(name=name, description=description)
    db.add(item)
    commit(db)
    db.refresh(item)
    return _response(item, 0)


def update(db: Session, collection_id: int, name: str | None, description: str | None, fields_set: set[str]) -> CollectionResponse:
    item = db.get(Collection, collection_id)
    if item is None:
        raise LookupError("Collection not found")
    if name is not None and db.query(Collection).filter(Collection.name == name, Collection.id != collection_id).first():
        raise FileExistsError("合集名已存在")
    if "name" in fields_set:
        item.name = name
    if "description" in fields_set:
        item.description = description
    commit(db)
    db.refresh(item)
    count = db.query(func.count(Message.id)).filter(Message.collection_id == collection_id).scalar() or 0
    return _response(item, count)


def delete(db: Session, collection_id: int) -> None:
    item = db.get(Collection, collection_id)
    if item is None:
        raise LookupError("Collection not found")
    db.query(Message).filter(Message.collection_id == collection_id).update({Message.collection_id: None}, synchronize_session=False)
    db.delete(item)
    commit(db)
