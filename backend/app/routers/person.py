from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import get_db, Person, media_person
from app.schemas.person import PersonResponse, PersonCreate, PersonUpdate
from typing import List, Optional

router = APIRouter(prefix="/people", tags=["people"])


def _person_response(person: Person, media_count: int) -> PersonResponse:
    return PersonResponse(
        id=person.id,
        name=person.name,
        description=person.description,
        cover_path=person.cover_path,
        media_count=media_count,
        created_at=person.created_at.isoformat(),
        updated_at=person.updated_at.isoformat(),
    )


@router.get("", response_model=List[PersonResponse])
def get_people(
    name: Optional[str] = Query(None, description="按名称模糊搜索"),
    db: Session = Depends(get_db),
):
    """获取所有人物，附带每个人物关联的媒体数量。"""
    count_sub = (
        db.query(media_person.c.person_id, func.count().label("cnt"))
        .group_by(media_person.c.person_id)
        .subquery()
    )
    query = (
        db.query(Person, func.coalesce(count_sub.c.cnt, 0).label("media_count"))
        .outerjoin(count_sub, Person.id == count_sub.c.person_id)
    )
    if name:
        query = query.filter(Person.name.ilike(f"%{name}%"))
    query = query.order_by(func.coalesce(count_sub.c.cnt, 0).desc())

    return [_person_response(person, count) for person, count in query.all()]


@router.post("", response_model=PersonResponse, status_code=201)
def create_person(
    data: PersonCreate,
    db: Session = Depends(get_db),
):
    """新建人物（名称唯一）"""
    existing = db.query(Person).filter(Person.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="人物名已存在")
    person = Person(name=data.name, description=data.description)
    db.add(person)
    db.commit()
    db.refresh(person)
    return _person_response(person, 0)


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(
    person_id: int,
    data: PersonUpdate,
    db: Session = Depends(get_db),
):
    """重命名 / 修改人物描述"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    if data.name is not None:
        dup = db.query(Person).filter(Person.name == data.name, Person.id != person_id).first()
        if dup:
            raise HTTPException(status_code=409, detail="人物名已存在")
        person.name = data.name
    if data.description is not None:
        person.description = data.description
    db.commit()
    db.refresh(person)
    count = db.query(func.count()).select_from(media_person).filter(media_person.c.person_id == person_id).scalar() or 0
    return _person_response(person, count)


@router.delete("/{person_id}", status_code=204)
def delete_person(
    person_id: int,
    db: Session = Depends(get_db),
):
    """删除人物及其媒体关联"""
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    db.execute(media_person.delete().where(media_person.c.person_id == person_id))
    db.delete(person)
    db.commit()
