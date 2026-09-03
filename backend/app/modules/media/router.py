import logging
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.models import get_db, Media
from typing import Optional, List

logger = logging.getLogger(__name__)
from app.modules.media.schemas import (
    MediaResponse,
    MediaDetailResponse,
    MediaCursorResponse,
    TimelineItem,
    VideoPreviewItem,
    VideoPreviewCreate,
    VideoPreviewUpdate,
    PeopleRequest, RotateRequest, TagsRequest,
)
from app.modules.media.service import (
    rotate_media,
    attach_existing_preview, attach_screenshot_preview, delete_media as delete_media_service,
    delete_preview as delete_preview_service, set_people, set_rating, set_starred,
    set_tags, update_preview as update_preview_service,
)
from app.modules.message import link_media_to_message
from app.modules.media.queries import (
    detail as media_detail, feed as media_feed, list_media, previews as media_previews, require_video, timeline,
)
from app.modules.media.file_service import replace_from_upload, set_cover

router = APIRouter(prefix="/media", tags=["media"])

@router.get("", response_model=MediaCursorResponse)
def get_media(
    cursor: Optional[str] = Query(None, description="游标，格式为'media_time|id'"),
    direction: Optional[str] = Query(None, description="分页方向: 'forward' 加载更新的媒体"),
    limit: int = Query(20, ge=1, le=100),
    message_id: Optional[int] = None,
    message_ids: Optional[List[int]] = Query(None, description="按多条 message 取并集过滤"),
    starred: Optional[bool] = Query(None),
    type: Optional[str] = Query(None, description="媒体类型: 'video'、'image' 或 'screenshot'"),
    tag_id: Optional[int] = Query(None, description="标签 ID"),
    collection_id: Optional[int] = Query(None, description="合集 ID"),
    has_physical_file: Optional[bool] = Query(None, description="是否存在已物化的物理文件"),
    db: Session = Depends(get_db)
):
    """获取媒体列表（游标分页，显示所有媒体）"""

    try:
        return list_media(
            db,
            cursor=cursor,
            direction=direction,
            limit=limit,
            message_id=message_id,
            message_ids=message_ids,
            starred=starred,
            media_type=type,
            tag_id=tag_id,
            collection_id=collection_id,
            has_physical_file=has_physical_file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@router.get("/timeline", response_model=list[TimelineItem])
def get_media_timeline(
    starred: Optional[bool] = Query(None),
    type: Optional[str] = Query(None, description="媒体类型: 'video'、'image' 或 'screenshot'"),
    tag_id: Optional[int] = Query(None),
    collection_id: Optional[int] = Query(None),
    has_physical_file: Optional[bool] = Query(None, description="是否存在已物化的物理文件"),
    db: Session = Depends(get_db)
):
    return timeline(
        db,
        starred=starred,
        media_type=type,
        tag_id=tag_id,
        collection_id=collection_id,
        has_physical_file=has_physical_file,
    )
@router.get("/feed", response_model=MediaCursorResponse)
def get_media_feed(
    cursor: Optional[int] = Query(None, description="游标：message_media.id"),
    limit: int = Query(40, ge=1, le=100),
    tag_id: Optional[int] = Query(None),
    collection_id: Optional[int] = Query(None),
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """按 MessageMedia 展开的媒体流（Telegram风格，媒体可重复），支持 tag/collection 筛选"""
    return media_feed(db, cursor=cursor, limit=limit, tag_id=tag_id, collection_id=collection_id, starred=starred)
# ===== 视频预览（章节）扁平路径端点（必须在 /{media_id} 之前声明） =====

@router.patch("/previews/{preview_id}", response_model=VideoPreviewItem)
def update_preview(preview_id: int, body: VideoPreviewUpdate, db: Session = Depends(get_db)):
    try:
        image = update_preview_service(db, preview_id, body.frame_ms, body.start_ms, body.end_ms)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VideoPreviewItem.model_validate(image)


@router.delete("/previews/{preview_id}", status_code=204)
def delete_preview(preview_id: int, db: Session = Depends(get_db)):
    try:
        delete_preview_service(db, preview_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return None


@router.get("/{media_id}", response_model=MediaDetailResponse)
def get_media_by_id(media_id: int, db: Session = Depends(get_db)):
    try: return media_detail(db, media_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.put("/{media_id}/starred")
def toggle_media_starred(
    media_id: int,
    starred: bool = Query(...),
    db: Session = Depends(get_db)
):
    """切换媒体收藏状态"""
    try:
        set_starred(db, media_id, starred)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"starred": starred}

@router.put("/{media_id}/rating")
def update_media_rating(
    media_id: int,
    rating: int = Query(..., ge=0, le=10),
    db: Session = Depends(get_db)
):
    """更新媒体评分"""
    try:
        set_rating(db, media_id, rating)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "Rating updated successfully", "rating": rating}


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
    except OSError as e:
        raise HTTPException(
            status_code=409,
            detail=f"无法删除源文件，请先停止播放或关闭占用该文件的程序：{e}",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{media_id}/replace", response_model=MediaResponse)
def replace_media_endpoint(
    media_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """用上传文件替换该 media 对应的实际文件，保留 Media 行 id 及所有关联。"""
    try:
        media = replace_from_upload(db, media_id, file.file, file.filename or "")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        file.file.close()

    return MediaResponse.model_validate(media)


@router.put("/{media_id}/tags")
def set_media_tags(
    media_id: int,
    body: TagsRequest,
    db: Session = Depends(get_db)
):
    try:
        tags = set_tags(db, media_id, body.tag_ids)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [{"id": t.id, "name": t.name, "category": t.category} for t in tags]


@router.put("/{media_id}/people")
def set_media_people(
    media_id: int,
    body: PeopleRequest,
    db: Session = Depends(get_db)
):
    """整体替换该 media 关联的人物集合。"""
    try:
        people = set_people(db, media_id, body.person_ids)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [{"id": p.id, "name": p.name} for p in people]


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
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if result["action"] == "unlinked":
        return {"message": "Media unlinked from message", "unlinked": True}
    return {"message": "Media deleted", "media_id": result["media_id"]}


# ===== 视频预览（章节）相关端点 =====

def _require_video(db: Session, media_id: int) -> Media:
    try: return require_video(db, media_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{media_id}/previews", response_model=List[VideoPreviewItem])
def list_previews(media_id: int, db: Session = Depends(get_db)):
    try: return media_previews(db, media_id)
    except LookupError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc: raise HTTPException(status_code=400, detail=str(exc)) from exc


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
        )
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower() or "找不到" in msg:
            raise HTTPException(status_code=404, detail=msg)
        if "already used" in msg.lower() or "已被" in msg:
            raise HTTPException(status_code=409, detail=msg)
        raise HTTPException(status_code=400, detail=msg)

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
    """把上传的图片设为当前视频缩略图。"""
    media = _require_video(db, media_id)

    try:
        ok = set_cover(media, file.file, file.filename or "")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update cover for media id={media_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update cover: {e}")
    finally:
        file.file.close()

    if not ok:
        logger.warning(f"Thumbnail regeneration failed for media id={media_id}")

    return {"message": "Cover updated", "ok": ok}


