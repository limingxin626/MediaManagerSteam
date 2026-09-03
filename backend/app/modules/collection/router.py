"""HTTP boundary for collections."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import get_db
from app.modules.collection import service
from app.modules.collection.schemas import CollectionCreate, CollectionListResponse, CollectionResponse, CollectionSyncResponse, CollectionUpdate

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/sync", response_model=List[CollectionSyncResponse])
def sync_collections(db: Session = Depends(get_db)):
    return service.sync(db)


@router.get("", response_model=CollectionListResponse)
def get_collections(name: Optional[str] = None, db: Session = Depends(get_db)):
    return service.list_collections(db, name)


@router.post("", response_model=CollectionResponse, status_code=201)
def create_collection(data: CollectionCreate, db: Session = Depends(get_db)):
    try:
        return service.create(db, data.name, data.description)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.put("/{collection_id}", response_model=CollectionResponse)
def update_collection(collection_id: int, data: CollectionUpdate, db: Session = Depends(get_db)):
    try:
        return service.update(db, collection_id, data.name, data.description, data.model_fields_set)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.delete("/{collection_id}", status_code=204)
def delete_collection(collection_id: int, db: Session = Depends(get_db)):
    try:
        service.delete(db, collection_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
