import os
import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, Integer
from app.models import get_db, Media, MessageMedia, Message, Tag, message_tag, media_tag
from typing import Optional, List, Literal
from app.schemas.media import (
    MediaResponse,
    MediaCursorResponse,
    TimelineItem,
    VideoPreviewItem,
    VideoPreviewCreate,
    VideoPreviewUpdate,
)
from app.config import AppConfig, config as app_config
from app.services.media_service import rotate_media, create_preview_media

router = APIRouter(prefix="/media", tags=["media"])

@router.get("", response_model=MediaCursorResponse)
def get_media(
    cursor: Optional[str] = Query(None, description="游标，格式为'created_at|position'"),
    direction: Optional[str] = Query(None, description="分页方向: 'forward' 加载更新的媒体"),
    limit: int = Query(20, ge=1, le=100),
    message_id: Optional[int] = None,
    starred: Optional[bool] = Query(None),
    type: Optional[str] = Query(None, description="媒体类型: 'video' 或 'image'"),
    tag_id: Optional[int] = Query(None, description="标签 ID"),
    actor_id: Optional[int] = Query(None, description="演员 ID"),
    db: Session = Depends(get_db)
):
    """获取媒体列表（游标分页，显示所有媒体）"""

    if message_id:
        # 通过 message_id 获取媒体
        media_relations = db.query(MessageMedia).filter(
            MessageMedia.message_id == message_id
        ).order_by(MessageMedia.position).all()
        
        media_ids = [relation.media_id for relation in media_relations]
        media = db.query(Media).filter(Media.id.in_(media_ids)).all()
        
        # 对于固定message_id的情况，返回简单的列表
        result = [MediaResponse.model_validate(item) for item in media]

        return MediaCursorResponse(
            items=result,
            next_cursor=None,
            has_more=False
        )
    else:
        # 直接查 Media 表，显示所有媒体（包括孤立媒体），但隐藏作为视频预览的 Media
        query = db.query(Media).filter(Media.video_media_id.is_(None))

        if starred is not None:
            query = query.filter(Media.starred == (1 if starred else 0))
        
        if type == 'video':
            query = query.filter(Media.mime_type.like('video/%'))
        elif type == 'image':
            query = query.filter(Media.mime_type.like('image/%'))

        if tag_id is not None:
            msg_ids = db.query(message_tag.c.message_id).filter(message_tag.c.tag_id == tag_id)
            media_ids_msg = db.query(MessageMedia.media_id.label('mid')).filter(MessageMedia.message_id.in_(msg_ids))
            media_ids_direct = db.query(media_tag.c.media_id.label('mid')).filter(media_tag.c.tag_id == tag_id)
            combined = media_ids_msg.union(media_ids_direct).subquery()
            query = query.filter(Media.id.in_(db.query(combined.c.mid)))

        if actor_id is not None:
            media_ids_actor = (
                db.query(MessageMedia.media_id)
                .join(Message, Message.id == MessageMedia.message_id)
                .filter(Message.actor_id == actor_id)
            )
            query = query.filter(Media.id.in_(media_ids_actor))

        # 游标格式："{created_at}|{id}"
        if cursor:
            try:
                parts = cursor.split('|')
                cursor_time = datetime.fromisoformat(parts[0])
                cursor_id = int(parts[1])

                if direction == 'around':
                    half = limit // 2
                    q_before = query.filter(
                        (Media.created_at > cursor_time) |
                        ((Media.created_at == cursor_time) & (Media.id >= cursor_id))
                    ).order_by(Media.created_at.asc(), Media.id.asc()).limit(half + 1).all()

                    q_after = query.filter(
                        (Media.created_at < cursor_time) |
                        ((Media.created_at == cursor_time) & (Media.id < cursor_id))
                    ).order_by(Media.created_at.desc(), Media.id.desc()).limit(limit - half + 1).all()

                    has_more_before = len(q_before) > half
                    before_items = q_before[:half]
                    before_items.reverse()

                    has_more = len(q_after) > (limit - half)
                    after_items = q_after[:(limit - half)]

                    items = before_items + after_items
                    next_cursor = None
                    prev_cursor = None
                    if has_more and items:
                        last = items[-1]
                        next_cursor = f"{last.created_at.isoformat()}|{last.id}"
                    if has_more_before and items:
                        first = items[0]
                        prev_cursor = f"{first.created_at.isoformat()}|{first.id}"

                    result = [MediaResponse.model_validate(item) for item in items]
                    return MediaCursorResponse(
                        items=result,
                        next_cursor=next_cursor,
                        prev_cursor=prev_cursor,
                        has_more=has_more,
                        has_more_before=has_more_before,
                    )

                elif direction == 'forward':
                    query = query.filter(
                        (Media.created_at > cursor_time) |
                        ((Media.created_at == cursor_time) & (Media.id > cursor_id))
                    )
                    query = query.order_by(Media.created_at.asc(), Media.id.asc())
                else:
                    query = query.filter(
                        (Media.created_at < cursor_time) |
                        ((Media.created_at == cursor_time) & (Media.id < cursor_id))
                    )
                    query = query.order_by(Media.created_at.desc(), Media.id.desc())
            except (ValueError, IndexError):
                raise HTTPException(status_code=400, detail="Invalid cursor format")
        else:
            query = query.order_by(Media.created_at.desc(), Media.id.desc())

        media_items = query.limit(limit + 1).all()

        has_more = len(media_items) > limit
        items = media_items[:limit]

        next_cursor = None
        if has_more and items:
            last = items[-1]
            next_cursor = f"{last.created_at.isoformat()}|{last.id}"

        result = [MediaResponse.model_validate(item) for item in items]

        return MediaCursorResponse(
            items=result,
            next_cursor=next_cursor,
            prev_cursor=None,
            has_more=has_more,
            has_more_before=False
        )

@router.get("/timeline", response_model=list[TimelineItem])
def get_media_timeline(
    starred: Optional[bool] = Query(None),
    type: Optional[str] = Query(None, description="媒体类型: 'video' 或 'image'"),
    tag_id: Optional[int] = Query(None),
    actor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    year_col = func.cast(func.strftime('%Y', Media.created_at), Integer)
    month_col = func.cast(func.strftime('%m', Media.created_at), Integer)

    query = db.query(
        year_col.label('year'),
        month_col.label('month'),
        func.count().label('count'),
    ).filter(Media.video_media_id.is_(None))

    if starred is not None:
        query = query.filter(Media.starred == (1 if starred else 0))
    if type == 'video':
        query = query.filter(Media.mime_type.like('video/%'))
    elif type == 'image':
        query = query.filter(Media.mime_type.like('image/%'))

    if tag_id is not None:
        msg_ids = db.query(message_tag.c.message_id).filter(message_tag.c.tag_id == tag_id)
        media_ids_msg = db.query(MessageMedia.media_id.label('mid')).filter(MessageMedia.message_id.in_(msg_ids))
        media_ids_direct = db.query(media_tag.c.media_id.label('mid')).filter(media_tag.c.tag_id == tag_id)
        combined = media_ids_msg.union(media_ids_direct).subquery()
        query = query.filter(Media.id.in_(db.query(combined.c.mid)))

    if actor_id is not None:
        media_ids_actor = (
            db.query(MessageMedia.media_id)
            .join(Message, Message.id == MessageMedia.message_id)
            .filter(Message.actor_id == actor_id)
        )
        query = query.filter(Media.id.in_(media_ids_actor))

    rows = query.group_by('year', 'month').order_by(
        year_col.desc(), month_col.desc()
    ).all()

    return [TimelineItem(year=r.year, month=r.month, count=r.count) for r in rows]


@router.get("/feed", response_model=MediaCursorResponse)
def get_media_feed(
    cursor: Optional[int] = Query(None, description="游标：message_media.id"),
    limit: int = Query(40, ge=1, le=100),
    tag_id: Optional[int] = Query(None),
    actor_id: Optional[int] = Query(None),
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """按 MessageMedia 展开的媒体流（Telegram风格，媒体可重复），支持 tag/actor 筛选"""
    query = (
        db.query(Media, MessageMedia)
        .join(MessageMedia, MessageMedia.media_id == Media.id)
        .join(Message, Message.id == MessageMedia.message_id)
    )

    if tag_id is not None:
        msg_with_tag = db.query(message_tag.c.message_id).filter(message_tag.c.tag_id == tag_id)
        media_with_tag = (
            db.query(MessageMedia.message_id)
            .join(media_tag, MessageMedia.media_id == media_tag.c.media_id)
            .filter(media_tag.c.tag_id == tag_id)
        )
        combined = msg_with_tag.union(media_with_tag).subquery()
        query = query.filter(Message.id.in_(db.query(combined.c.message_id)))

    if actor_id is not None:
        query = query.filter(Message.actor_id == actor_id)

    if starred is not None:
        query = query.filter(Media.starred == (1 if starred else 0))

    if cursor is not None:
        query = query.filter(MessageMedia.id < cursor)

    query = query.order_by(MessageMedia.id.desc())

    rows = query.limit(limit + 1).all()

    has_more = len(rows) > limit
    rows = rows[:limit]

    next_cursor = str(rows[-1][1].id) if has_more and rows else None

    result = [MediaResponse.model_validate(media) for media, _ in rows]

    return MediaCursorResponse(
        items=result,
        next_cursor=next_cursor,
        has_more=has_more,
    )


# ===== 视频预览（章节）扁平路径端点（必须在 /{media_id} 之前声明） =====

def _validate_range(frame_ms: Optional[int], start_ms: Optional[int], end_ms: Optional[int]) -> None:
    if frame_ms is not None and frame_ms < 0:
        raise HTTPException(status_code=400, detail="frame_ms must be >= 0")
    if start_ms is not None and start_ms < 0:
        raise HTTPException(status_code=400, detail="start_ms must be >= 0")
    if end_ms is not None and end_ms < 0:
        raise HTTPException(status_code=400, detail="end_ms must be >= 0")
    if start_ms is not None and end_ms is not None and start_ms > end_ms:
        raise HTTPException(status_code=400, detail="start_ms must be <= end_ms")


@router.patch("/previews/{preview_id}", response_model=VideoPreviewItem)
def update_preview(preview_id: int, body: VideoPreviewUpdate, db: Session = Depends(get_db)):
    image = db.query(Media).filter(Media.id == preview_id).first()
    if not image or image.video_media_id is None:
        raise HTTPException(status_code=404, detail="Preview not found")
    new_frame = body.frame_ms if body.frame_ms is not None else image.frame_ms
    new_start = body.start_ms if body.start_ms is not None else image.start_ms
    new_end = body.end_ms if body.end_ms is not None else image.end_ms
    _validate_range(new_frame, new_start, new_end)
    if body.frame_ms is not None:
        image.frame_ms = body.frame_ms
    if body.start_ms is not None:
        image.start_ms = body.start_ms
    if body.end_ms is not None:
        image.end_ms = body.end_ms
    db.commit()
    db.refresh(image)
    return VideoPreviewItem.model_validate(image)


@router.delete("/previews/{preview_id}", status_code=204)
def delete_preview(preview_id: int, db: Session = Depends(get_db)):
    image = db.query(Media).filter(Media.id == preview_id).first()
    if not image or image.video_media_id is None:
        raise HTTPException(status_code=404, detail="Preview not found")
    file_path = image.file_path
    db.delete(image)
    db.commit()

    thumb_path = AppConfig.get_thumbnail_path(preview_id)
    if os.path.exists(thumb_path):
        try:
            os.remove(thumb_path)
        except Exception:
            pass
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception:
            pass
    return None


@router.get("/{media_id}", response_model=MediaResponse)
def get_media_by_id(media_id: int, db: Session = Depends(get_db)):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    return MediaResponse.model_validate(media)


@router.put("/{media_id}/starred")
def toggle_media_starred(
    media_id: int,
    starred: bool = Query(...),
    db: Session = Depends(get_db)
):
    """切换媒体收藏状态"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media.starred = 1 if starred else 0
    db.commit()

    return {"starred": starred}

@router.put("/{media_id}/rating")
def update_media_rating(
    media_id: int,
    rating: int = Query(..., ge=0, le=10),
    db: Session = Depends(get_db)
):
    """更新媒体评分"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    media.rating = rating
    db.commit()

    return {"message": "Rating updated successfully", "rating": rating}

class RotateRequest(BaseModel):
    degrees: Literal[90, 180, 270]


@router.post("/{media_id}/rotate", response_model=MediaResponse)
def rotate_media_endpoint(
    media_id: int,
    body: RotateRequest,
    db: Session = Depends(get_db)
):
    try:
        media = rotate_media(db, media_id, body.degrees)
        return MediaResponse.model_validate(media)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


class TagsRequest(BaseModel):
    tag_ids: List[int]


@router.put("/{media_id}/tags")
def set_media_tags(
    media_id: int,
    body: TagsRequest,
    db: Session = Depends(get_db)
):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    tags = db.query(Tag).filter(Tag.id.in_(body.tag_ids)).all()
    media.tags = tags
    db.commit()
    return [{"id": t.id, "name": t.name, "category": t.category} for t in media.tags]


@router.delete("/{media_id}")
def delete_media(
    media_id: int,
    delete_source: bool = Query(False, description="是否同时删除源文件"),
    message_id: Optional[int] = Query(None, description="来源消息ID，传入时仅在无其他关联时才删除媒体本身"),
    db: Session = Depends(get_db)
):
    """删除媒体。若指定 message_id 且该媒体被多条消息引用，则仅解除当前关联。"""
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")

    if message_id is not None:
        ref_count = db.query(MessageMedia).filter(MessageMedia.media_id == media_id).count()
        if ref_count > 1:
            db.query(MessageMedia).filter(
                MessageMedia.media_id == media_id,
                MessageMedia.message_id == message_id
            ).delete()
            db.commit()
            return {"message": "Media unlinked from message", "unlinked": True}

    file_path = media.file_path

    db.query(MessageMedia).filter(MessageMedia.media_id == media_id).delete()
    db.execute(media_tag.delete().where(media_tag.c.media_id == media_id))
    db.delete(media)
    db.commit()

    thumb_path = AppConfig.get_thumbnail_path(media_id)
    if os.path.exists(thumb_path):
        try:
            os.remove(thumb_path)
        except Exception as e:
            print(f"删除缩略图失败: {e}")

    if delete_source and file_path:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"成功删除源文件: {file_path}")
        except Exception as e:
            print(f"删除源文件失败: {e}")

    return {"message": "Media deleted successfully", "unlinked": False}


# ===== 视频预览（章节）相关端点 =====

def _require_video(db: Session, media_id: int) -> Media:
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    if not (media.mime_type or "").startswith("video/"):
        raise HTTPException(status_code=400, detail="Target media is not a video")
    return media


@router.get("/{media_id}/previews", response_model=List[VideoPreviewItem])
def list_previews(media_id: int, db: Session = Depends(get_db)):
    _require_video(db, media_id)
    rows = (
        db.query(Media)
        .filter(Media.video_media_id == media_id)
        .order_by(Media.frame_ms.asc())
        .all()
    )
    return [VideoPreviewItem.model_validate(r) for r in rows]


@router.post("/{media_id}/previews", response_model=VideoPreviewItem)
def add_preview(media_id: int, body: VideoPreviewCreate, db: Session = Depends(get_db)):
    _require_video(db, media_id)
    if body.preview_media_id == media_id:
        raise HTTPException(status_code=400, detail="preview_media_id cannot equal video media id")
    image = db.query(Media).filter(Media.id == body.preview_media_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Preview media not found")
    if not (image.mime_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Preview media must be an image")
    if image.video_media_id is not None:
        raise HTTPException(status_code=409, detail="Preview media is already used by another video")
    _validate_range(body.frame_ms, body.start_ms, body.end_ms)

    image.video_media_id = media_id
    image.frame_ms = body.frame_ms
    image.start_ms = body.start_ms
    image.end_ms = body.end_ms
    db.commit()
    db.refresh(image)
    return VideoPreviewItem.model_validate(image)


@router.post("/{media_id}/previews/screenshot", response_model=VideoPreviewItem)
def add_preview_from_screenshot(
    media_id: int,
    file: UploadFile = File(...),
    frame_ms: int = Form(...),
    start_ms: Optional[int] = Form(None),
    end_ms: Optional[int] = Form(None),
    db: Session = Depends(get_db),
):
    _require_video(db, media_id)
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image")
    _validate_range(frame_ms, start_ms, end_ms)

    upload_dir = app_config.get_upload_dir()
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    if ext not in (".jpg", ".jpeg", ".png", ".webp"):
        ext = ".jpg"
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    base = f"preview_{media_id}_{timestamp}{ext}"
    dest_path = os.path.join(upload_dir, base)
    counter = 1
    while os.path.exists(dest_path):
        dest_path = os.path.join(upload_dir, f"preview_{media_id}_{timestamp}_{counter}{ext}")
        counter += 1
    with open(dest_path, "wb") as f:
        f.write(file.file.read())

    try:
        image = create_preview_media(db, dest_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    image.video_media_id = media_id
    image.frame_ms = frame_ms
    image.start_ms = start_ms
    image.end_ms = end_ms
    db.flush()

    earliest_mm = (
        db.query(MessageMedia)
        .filter(MessageMedia.media_id == media_id)
        .order_by(MessageMedia.created_at.asc(), MessageMedia.id.asc())
        .first()
    )
    if earliest_mm is not None:
        target_message_id = earliest_mm.message_id
        max_position = (
            db.query(func.coalesce(func.max(MessageMedia.position), -1))
            .filter(MessageMedia.message_id == target_message_id)
            .scalar()
        )
        db.add(MessageMedia(
            message_id=target_message_id,
            media_id=image.id,
            position=int(max_position) + 1,
        ))

    db.commit()
    db.refresh(image)
    return VideoPreviewItem.model_validate(image)


