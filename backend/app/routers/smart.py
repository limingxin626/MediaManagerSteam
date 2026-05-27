"""智能查询路由：tag 建议、相似媒体、文本搜索、embedding 重建。"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import get_db, Media
from app.schemas.media import MediaResponse, MediaCursorResponse
from app.services import clip_service, smart_tag_service

router = APIRouter(prefix="/smart", tags=["smart"])


class SuggestRequest(BaseModel):
    media_id: int
    top_k: int = 10


class TagSuggestion(BaseModel):
    tag_id: int
    name: str
    category: Optional[str] = None
    score: float


class ApplyRequest(BaseModel):
    media_id: int
    tag_ids: List[int]


class RebuildRequest(BaseModel):
    media_ids: Optional[List[int]] = None


def _require_clip() -> None:
    if not clip_service.is_available():
        raise HTTPException(status_code=503, detail=f"CLIP 模型不可用: {clip_service.get_unavailable_reason()}")


@router.get("/status")
def smart_status():
    available = clip_service.is_available()
    return {
        "available": available,
        "model": clip_service.MODEL_NAME,
        "reason": None if available else clip_service.get_unavailable_reason(),
    }


@router.post("/tags/suggest", response_model=List[TagSuggestion])
def suggest_tags(body: SuggestRequest, db: Session = Depends(get_db)):
    _require_clip()
    try:
        return smart_tag_service.suggest_tags(db, body.media_id, top_k=body.top_k)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tags/apply", response_model=List[dict])
def apply_tags(body: ApplyRequest, db: Session = Depends(get_db)):
    try:
        tags = smart_tag_service.apply_tags(db, body.media_id, body.tag_ids)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return [{"id": t.id, "name": t.name, "category": t.category} for t in tags]


def _fetch_media_in_order(db: Session, scored: List[dict]) -> List[Media]:
    if not scored:
        return []
    ids = [s["media_id"] for s in scored]
    rows = db.query(Media).filter(Media.id.in_(ids)).all()
    by_id = {m.id: m for m in rows}
    ordered: List[Media] = []
    for s in scored:
        m = by_id.get(s["media_id"])
        if m is not None:
            ordered.append(m)
    return ordered


@router.get("/similar/{media_id}", response_model=MediaCursorResponse)
def similar_media(
    media_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    _require_clip()
    try:
        scored = smart_tag_service.find_similar(db, media_id, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    ordered = _fetch_media_in_order(db, scored)
    items = [MediaResponse.model_validate(m) for m in ordered]
    return MediaCursorResponse(items=items, next_cursor=None, has_more=False)


@router.get("/search", response_model=MediaCursorResponse)
def search_media(
    q: str = Query(..., min_length=1, description="自然语言/标签关键词"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    _require_clip()
    scored = smart_tag_service.search_by_text(db, q, limit=limit)
    ordered = _fetch_media_in_order(db, scored)
    items = [MediaResponse.model_validate(m) for m in ordered]
    return MediaCursorResponse(items=items, next_cursor=None, has_more=False)


@router.post("/embeddings/rebuild")
def rebuild_embeddings(body: RebuildRequest, db: Session = Depends(get_db)):
    _require_clip()
    return smart_tag_service.rebuild_embeddings(db, media_ids=body.media_ids)
