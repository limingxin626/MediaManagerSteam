"""Person queries and mutation use cases."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Person, media_person
from app.modules.person.schemas import PersonResponse
from app.shared.unit_of_work import commit


def _response(person: Person, count: int) -> PersonResponse:
    return PersonResponse(id=person.id, name=person.name, description=person.description, cover_path=person.cover_path, media_count=count, created_at=person.created_at.isoformat(), updated_at=person.updated_at.isoformat())


def list_people(db: Session, name: str | None) -> list[PersonResponse]:
    counts = db.query(media_person.c.person_id, func.count().label("cnt")).group_by(media_person.c.person_id).subquery()
    total = func.coalesce(counts.c.cnt, 0)
    query = db.query(Person, total).outerjoin(counts, Person.id == counts.c.person_id)
    if name:
        query = query.filter(Person.name.ilike(f"%{name}%"))
    return [_response(person, count) for person, count in query.order_by(total.desc()).all()]


def create(db: Session, name: str, description: str | None) -> PersonResponse:
    if db.query(Person).filter(Person.name == name).first():
        raise FileExistsError("人物名已存在")
    person = Person(name=name, description=description)
    db.add(person); commit(db); db.refresh(person)
    return _response(person, 0)


def update(db: Session, person_id: int, name: str | None, description: str | None, fields_set: set[str]) -> PersonResponse:
    person = db.get(Person, person_id)
    if person is None:
        raise LookupError("Person not found")
    if name is not None and db.query(Person).filter(Person.name == name, Person.id != person_id).first():
        raise FileExistsError("人物名已存在")
    if "name" in fields_set: person.name = name
    if "description" in fields_set: person.description = description
    commit(db); db.refresh(person)
    count = db.query(func.count()).select_from(media_person).filter(media_person.c.person_id == person_id).scalar() or 0
    return _response(person, count)


def delete(db: Session, person_id: int) -> None:
    person = db.get(Person, person_id)
    if person is None:
        raise LookupError("Person not found")
    db.execute(media_person.delete().where(media_person.c.person_id == person_id)); db.delete(person); commit(db)
