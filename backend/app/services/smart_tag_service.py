"""智能 tag / 相似搜索服务。

特性：
  - 复用 CLIP 图像 embedding 做 tag 建议、相似媒体、文本搜索
  - embedding 缓存到 `media_embedding` 表（float16 BLOB）
  - 候选 tag 仅来自库内已存在的 Tag.name
"""
from __future__ import annotations

import logging
import os
from typing import List, Optional, Tuple

import numpy as np
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import config
from app.models import Media, MediaEmbedding, Tag, message_tag, media_tag, MessageMedia
from app.services import clip_service

logger = logging.getLogger(__name__)


def _load_embedding(db: Session, media_id: int) -> Optional[np.ndarray]:
    row = db.query(MediaEmbedding).filter(MediaEmbedding.media_id == media_id).first()
    if row is None:
        return None
    return clip_service.bytes_to_vector(row.vector)


def _save_embedding(db: Session, media_id: int, vec: np.ndarray) -> None:
    data = clip_service.vector_to_bytes(vec)
    existing = db.query(MediaEmbedding).filter(MediaEmbedding.media_id == media_id).first()
    if existing is None:
        db.add(MediaEmbedding(media_id=media_id, model=clip_service.MODEL_NAME, vector=data))
    else:
        existing.model = clip_service.MODEL_NAME
        existing.vector = data


def ensure_embedding(db: Session, media_id: int) -> np.ndarray:
    """读缓存，没有就用缩略图计算并写库。返回 (512,) float32。"""
    cached = _load_embedding(db, media_id)
    if cached is not None:
        return cached

    media = db.query(Media).filter(Media.id == media_id).first()
    if media is None:
        raise ValueError(f"Media {media_id} not found")

    thumb_path = config.get_thumbnail_path(media_id)
    if not os.path.isfile(thumb_path):
        # 缩略图丢失，回退到原文件（可能是大视频，CLIP 也能处理首帧/单图）
        media_abs = config.resolve_to_absolute(media.repo_id, media.file_path)
        if not media_abs or not os.path.isfile(media_abs):
            raise ValueError(f"Media {media_id} 无可用图像文件")
        src_path = media_abs if (media.mime_type or "").startswith("image/") else thumb_path
    else:
        src_path = thumb_path

    if not os.path.isfile(src_path):
        raise ValueError(f"Media {media_id} 无缩略图，无法计算 embedding")

    vec = clip_service.encode_image(src_path)
    _save_embedding(db, media_id, vec)
    db.commit()
    return vec


def _candidate_tags(db: Session, limit: int = 200) -> List[Tag]:
    """取库内使用最多的前 N 个 tag 作为候选词表。"""
    msg_count = (
        db.query(message_tag.c.tag_id, func.count().label("cnt"))
        .group_by(message_tag.c.tag_id)
        .subquery()
    )
    media_count = (
        db.query(media_tag.c.tag_id, func.count().label("cnt"))
        .group_by(media_tag.c.tag_id)
        .subquery()
    )
    total = (func.coalesce(msg_count.c.cnt, 0) + func.coalesce(media_count.c.cnt, 0)).label("total")
    rows = (
        db.query(Tag, total)
        .outerjoin(msg_count, Tag.id == msg_count.c.tag_id)
        .outerjoin(media_count, Tag.id == media_count.c.tag_id)
        .order_by(total.desc())
        .limit(limit)
        .all()
    )
    return [t for t, _ in rows]


def suggest_tags(db: Session, media_id: int, top_k: int = 10) -> List[dict]:
    """返回 [{tag_id, name, category, score}] 按 score 降序。"""
    img_vec = ensure_embedding(db, media_id)
    candidates = _candidate_tags(db)
    if not candidates:
        return []

    scores: List[Tuple[Tag, float]] = []
    for tag in candidates:
        # 用 "a photo of {name}" 模板可微提升零样本效果，名字本身已含语义就直接用
        text_vec = clip_service.encode_text(tag.name)
        s = float(np.dot(img_vec, text_vec))
        scores.append((tag, s))

    scores.sort(key=lambda x: x[1], reverse=True)
    return [
        {"tag_id": t.id, "name": t.name, "category": t.category, "score": round(s, 4)}
        for t, s in scores[:top_k]
    ]


def _load_all_embeddings(db: Session, exclude_id: Optional[int] = None) -> Tuple[List[int], np.ndarray]:
    """返回 (media_ids, matrix (N,512))。仅包含非预览帧媒体。"""
    q = (
        db.query(MediaEmbedding.media_id, MediaEmbedding.vector)
        .join(Media, Media.id == MediaEmbedding.media_id)
        .filter(Media.video_media_id.is_(None))
    )
    if exclude_id is not None:
        q = q.filter(MediaEmbedding.media_id != exclude_id)
    rows = q.all()
    if not rows:
        return [], np.zeros((0, clip_service.EMBED_DIM), dtype=np.float32)
    ids = [r.media_id for r in rows]
    mat = np.stack([clip_service.bytes_to_vector(r.vector) for r in rows], axis=0)
    return ids, mat


def find_similar(db: Session, media_id: int, limit: int = 50) -> List[dict]:
    """返回 [{media_id, score}] 按 cosine 降序。"""
    target = ensure_embedding(db, media_id)
    ids, mat = _load_all_embeddings(db, exclude_id=media_id)
    if not ids:
        return []
    scores = mat @ target  # 已归一化 → 点积即 cosine
    order = np.argsort(-scores)[:limit]
    return [{"media_id": ids[i], "score": float(scores[i])} for i in order]


def search_by_text(db: Session, text: str, limit: int = 50) -> List[dict]:
    text = text.strip()
    if not text:
        return []
    qvec = clip_service.encode_text(text)
    ids, mat = _load_all_embeddings(db)
    if not ids:
        return []
    scores = mat @ qvec
    order = np.argsort(-scores)[:limit]
    return [{"media_id": ids[i], "score": float(scores[i])} for i in order]


def rebuild_embeddings(db: Session, media_ids: Optional[List[int]] = None) -> dict:
    """批量计算缺失的 embedding。返回 {processed, skipped, failed}。"""
    q = db.query(Media.id).filter(Media.video_media_id.is_(None))
    if media_ids is not None:
        q = q.filter(Media.id.in_(media_ids))
    all_ids = [r[0] for r in q.all()]

    existing = {
        r[0] for r in db.query(MediaEmbedding.media_id).filter(MediaEmbedding.media_id.in_(all_ids)).all()
    } if media_ids is None else set()
    # 若指定了 media_ids，强制重算更直观；不指定时只补缺失。
    todo = all_ids if media_ids is not None else [i for i in all_ids if i not in existing]

    processed = 0
    failed = 0
    for mid in todo:
        try:
            ensure_embedding(db, mid)
            processed += 1
        except Exception as e:
            logger.warning("embedding 失败 media_id=%s: %s", mid, e)
            failed += 1
    return {"processed": processed, "skipped": len(all_ids) - len(todo), "failed": failed, "total": len(all_ids)}


def apply_tags(db: Session, media_id: int, tag_ids: List[int]) -> List[Tag]:
    """把 tag_ids 追加到 media（不替换现有 tag）。返回当前完整 tag 列表。"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if media is None:
        raise ValueError("Media not found")
    new_tags = db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
    existing_ids = {t.id for t in media.tags}
    for t in new_tags:
        if t.id not in existing_ids:
            media.tags.append(t)
    db.commit()
    db.refresh(media)
    return list(media.tags)
