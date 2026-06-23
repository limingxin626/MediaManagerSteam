import os
import shutil
import time
from datetime import datetime
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, Integer
from app.models import get_db, Media, MessageMedia, Message, Tag, message_tag, media_tag
from typing import Optional, List, Literal

logger = logging.getLogger(__name__)
from app.schemas.media import (
    MediaResponse,
    MediaDetailResponse,
    MediaCursorResponse,
    TimelineItem,
    VideoPreviewItem,
    VideoPreviewCreate,
    VideoPreviewUpdate,
)
from app.config import AppConfig, config as app_config
from app.services.media_service import (
    rotate_media, create_preview_media, replace_media_file,
    attach_existing_preview, attach_screenshot_preview, delete_media as delete_media_service,
)
from app.services.message_service import link_media_to_message
from app.utils import ThumbnailUtils

router = APIRouter(prefix="/media", tags=["media"])

@router.get("", response_model=MediaCursorResponse)
def get_media(
    cursor: Optional[str] = Query(None, description="游标，格式为'created_at|position'"),
    direction: Optional[str] = Query(None, description="分页方向: 'forward' 加载更新的媒体"),
    limit: int = Query(20, ge=1, le=100),
    message_id: Optional[int] = None,
    message_ids: Optional[List[int]] = Query(None, description="按多条 message 取并集过滤"),
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

        if message_ids:
            media_ids_msgs = db.query(MessageMedia.media_id).filter(
                MessageMedia.message_id.in_(message_ids)
            )
            query = query.filter(Media.id.in_(media_ids_msgs))

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
    day_col = func.cast(func.strftime('%d', Media.created_at), Integer)

    query = db.query(
        year_col.label('year'),
        month_col.label('month'),
        day_col.label('day'),
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

    rows = query.group_by('year', 'month', 'day').order_by(
        year_col.desc(), month_col.desc(), day_col.desc()
    ).all()

    return [TimelineItem(year=r.year, month=r.month, day=r.day, count=r.count) for r in rows]


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
    file_path = AppConfig.resolve_to_absolute(image.repo_id, image.file_path)
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


@router.get("/{media_id}", response_model=MediaDetailResponse)
def get_media_by_id(media_id: int, db: Session = Depends(get_db)):
    media = db.query(Media).filter(Media.id == media_id).first()
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    message_ids = [
        mid for (mid,) in db.query(MessageMedia.message_id)
        .filter(MessageMedia.media_id == media_id)
        .distinct()
        .all()
    ]
    data = MediaResponse.model_validate(media).model_dump()
    data["messages"] = [{"id": mid} for mid in message_ids]
    return MediaDetailResponse(**data)


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
        media = rotate_media(db, media_id, body.degrees, commit=False)
        db.commit()
        db.refresh(media)
        return MediaResponse.model_validate(media)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{media_id}/replace", response_model=MediaResponse)
def replace_media_endpoint(
    media_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """用上传文件替换该 media 对应的实际文件，保留 Media 行 id 及所有关联。"""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if app_config.get_media_type(f"x{ext}") is None:
        raise HTTPException(status_code=400, detail="Unsupported media type")

    upload_dir = app_config.get_upload_dir()
    os.makedirs(upload_dir, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    tmp_path = os.path.join(upload_dir, f"replace_{media_id}_{timestamp}{ext}")
    counter = 1
    while os.path.exists(tmp_path):
        tmp_path = os.path.join(upload_dir, f"replace_{media_id}_{timestamp}_{counter}{ext}")
        counter += 1

    import shutil as _shutil
    try:
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f, length=1024 * 1024)
    except Exception:
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except Exception: pass
        raise

    try:
        media = replace_media_file(db, media_id, tmp_path, commit=False)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(tmp_path):
            try: os.remove(tmp_path)
            except Exception: pass

    db.commit()
    db.refresh(media)
    return MediaResponse.model_validate(media)


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
    try:
        result = delete_media_service(
            db,
            media_id=media_id,
            unlink_from_message_id=message_id,
            delete_source_file=delete_source,
            commit=True,  # service 内部管事务 + 文件清理
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if result["action"] == "unlinked":
        return {"message": "Media unlinked from message", "unlinked": True}
    return {"message": "Media deleted", "media_id": result["media_id"]}


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
    try:
        image = attach_existing_preview(
            db,
            video_media_id=media_id,
            preview_media_id=body.preview_media_id,
            frame_ms=body.frame_ms,
            start_ms=body.start_ms,
            end_ms=body.end_ms,
            commit=False,
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower() or "找不到" in msg:
            raise HTTPException(status_code=404, detail=msg)
        if "already used" in msg.lower() or "已被" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

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
    try:
        image = attach_screenshot_preview(
            db,
            video_media_id=media_id,
            file_obj=file.file,
            filename=file.filename or "",
            content_type=file.content_type or "",
            frame_ms=frame_ms,
            start_ms=start_ms,
            end_ms=end_ms,
            commit=True,  # service 内部管事务 + rename
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VideoPreviewItem.model_validate(image)


@router.post("/{media_id}/cover")
def set_video_cover(
    media_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """把上传的图片设为视频封面。

    落地策略遵循既有 sidecar 约定:`<stem>.cover.jpg` 写在视频同目录,
    并立刻基于这张 sidecar 重生成 `DATA_ROOT/thumbs/{id}.webp`。
    下次 re-import / replace 同一路径时,sidecar 仍会被自动识别,封面不会丢。
    """
    media = _require_video(db, media_id)

    abs_path = AppConfig.resolve_to_absolute(media.repo_id, media.file_path)
    if not abs_path or not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    folder, name = os.path.split(abs_path)
    stem = os.path.splitext(name)[0]
    sidecar_path = os.path.join(folder, f"{stem}.cover.jpg")

    try:
        with open(sidecar_path, "wb") as f:
            shutil.copyfileobj(file.file, f, length=1024 * 1024)
    except Exception as e:
        logger.error(f"Failed to write cover sidecar for media id={media_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write cover: {e}")

    thumb_path = AppConfig.get_thumbnail_path(media.id)
    ok = ThumbnailUtils.generate_image_thumbnail(sidecar_path, thumb_path)
    if not ok:
        logger.warning(f"Sidecar written but thumbnail regen failed for media id={media_id}")

    return {"message": "Cover updated", "sidecar": sidecar_path, "ok": ok}


