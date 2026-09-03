"""HTTP boundary for tags."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.models import get_db
from app.modules.tag import service
from app.modules.tag.schemas import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=List[TagResponse])
def get_tags(name: Optional[str] = Query(None, description="按名称模糊搜索"), has_media: bool = Query(False, description="只返回关联了媒体的标签"), db: Session = Depends(get_db)):
    return service.list_tags(db, name, has_media)


@router.post("", response_model=TagResponse, status_code=201)
def create_tag(data: TagCreate, db: Session = Depends(get_db)):
    try: return service.create(db, data.name, data.category)
    except FileExistsError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(tag_id: int, data: TagUpdate, db: Session = Depends(get_db)):
    try: return service.update(db, tag_id, data.name, data.category, data.model_fields_set)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileExistsError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{tag_id}", status_code=204)
def delete_tag(tag_id: int, db: Session = Depends(get_db)):
    try: service.delete(db, tag_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
