"""Person queries and mutation use cases."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Person, folder_person, media_person
from app.modules.person.schemas import PersonResponse
from app.shared.unit_of_work import commit


def _response(person: Person, media_count: int, folder_count: int) -> PersonResponse:
    return PersonResponse(
        id=person.id,
        name=person.name,
        description=person.description,
        cover_path=person.cover_path,
        media_count=media_count,
        folder_count=folder_count,
        created_at=person.created_at.isoformat(),
        updated_at=person.updated_at.isoformat(),
    )


def _counts(db: Session, person_id: int) -> tuple[int, int]:
    media_count = (
        db.query(func.count()).select_from(media_person)
        .filter(media_person.c.person_id == person_id).scalar() or 0
    )
    folder_count = (
        db.query(func.count()).select_from(folder_person)
        .filter(folder_person.c.person_id == person_id).scalar() or 0
    )
    return media_count, folder_count


def list_people(db: Session, name: str | None) -> list[PersonResponse]:
    media_counts = (
        db.query(media_person.c.person_id, func.count().label("cnt"))
        .group_by(media_person.c.person_id).subquery()
    )
    folder_counts = (
        db.query(folder_person.c.person_id, func.count().label("cnt"))
        .group_by(folder_person.c.person_id).subquery()
    )
    media_total = func.coalesce(media_counts.c.cnt, 0)
    folder_total = func.coalesce(folder_counts.c.cnt, 0)
    query = (
        db.query(Person, media_total, folder_total)
        .outerjoin(media_counts, Person.id == media_counts.c.person_id)
        .outerjoin(folder_counts, Person.id == folder_counts.c.person_id)
    )
    if name:
        query = query.filter(Person.name.ilike(f"%{name}%"))
    # 人物列表按参演作品(folder)数排序;同作品数退到媒体标注数,再按名称稳定排序。
    return [
        _response(person, int(media_count), int(folder_count))
        for person, media_count, folder_count in query.order_by(
            folder_total.desc(), media_total.desc(), Person.name,
        ).all()
    ]


def get(db: Session, person_id: int) -> PersonResponse:
    person = db.get(Person, person_id)
    if person is None:
        raise LookupError("Person not found")
    media_count, folder_count = _counts(db, person_id)
    return _response(person, media_count, folder_count)


def create(db: Session, name: str, description: str | None) -> PersonResponse:
    if db.query(Person).filter(Person.name == name).first():
        raise FileExistsError("人物名已存在")
    person = Person(name=name, description=description)
    db.add(person); commit(db); db.refresh(person)
    return _response(person, 0, 0)


def update(db: Session, person_id: int, name: str | None, description: str | None, fields_set: set[str]) -> PersonResponse:
    person = db.get(Person, person_id)
    if person is None:
        raise LookupError("Person not found")
    if name is not None and db.query(Person).filter(Person.name == name, Person.id != person_id).first():
        raise FileExistsError("人物名已存在")
    if "name" in fields_set: person.name = name
    if "description" in fields_set: person.description = description
    commit(db); db.refresh(person)
    media_count, folder_count = _counts(db, person_id)
    return _response(person, media_count, folder_count)


def delete(db: Session, person_id: int) -> None:
    person = db.get(Person, person_id)
    if person is None:
        raise LookupError("Person not found")
    db.execute(media_person.delete().where(media_person.c.person_id == person_id))
    db.execute(folder_person.delete().where(folder_person.c.person_id == person_id))
    db.delete(person); commit(db)
