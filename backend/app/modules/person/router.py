"""HTTP boundary for people."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.person import service
from app.modules.person.schemas import PersonCreate, PersonResponse, PersonUpdate

router = APIRouter(prefix="/people", tags=["people"])


@router.get("", response_model=List[PersonResponse])
def get_people(
    name: Optional[str] = Query(None, description="按名称模糊搜索"),
    db: Session = Depends(get_db),
):
    return service.list_people(db, name)


@router.get("/{person_id}", response_model=PersonResponse)
def get_person(person_id: int, db: Session = Depends(get_db)):
    try:
        return service.get(db, person_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=PersonResponse, status_code=201)
def create_person(data: PersonCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, data.name, data.description)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{person_id}", response_model=PersonResponse)
def update_person(person_id: int, data: PersonUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(
            db, person_id, data.name, data.description, data.model_fields_set
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{person_id}", status_code=204)
def delete_person(person_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, person_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
