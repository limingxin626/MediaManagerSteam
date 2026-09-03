from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Message, MessageMedia, Tag, get_db, media_tag, message_tag
from app.modules.media import process_file
from app.modules.message.queries import (
    aggregate_tags as _domain_aggregate_tags,
)
from app.modules.message.queries import (
    aggregate_tags_raw as _domain_aggregate_tags_raw,
)
from app.modules.message.queries import (
    batch_media_items as _domain_batch_media_items,
)
from app.modules.message.queries import (
    build_detail_query as _domain_build_detail_query,
)
from app.modules.message.queries import (
    build_detail_response as _domain_build_detail_response,
)
from app.modules.message.queries import (
    build_message_query as _domain_build_message_query,
)
from app.modules.message.queries import (
    build_sync_response as _domain_build_sync_response,
)
from app.modules.message.queries import (
    folder_fields as _domain_folder_fields,
)
from app.modules.message.queries import (
    folder_items as _domain_folder_items,
)
from app.modules.message.queries import (
    get_detail as query_message_detail,
)
from app.modules.message.queries import (
    get_detail_after_write,
    message_dates,
    sync_all,
)
from app.modules.message.queries import (
    list_messages as query_messages,
)
from app.modules.message.queries import (
    media_items_for as _domain_media_items_for,
)
from app.modules.message.queries import (
    paginate as _domain_paginate,
)
from app.modules.message.queries import (
    parse_cursor as _domain_parse_cursor,
)
from app.modules.message.queries import (
    search as search_messages,
)
from app.modules.message.queries import (
    sync_media_item as _domain_sync_media_item,
)
from app.modules.message.schemas import (
    MEDIA_PREVIEW_LIMIT,
    CursorResponse,
    MessageCreate,
    MessageCreateFromClient,
    MessageDateCount,
    MessageDatesResponse,
    MessageDetailCursorResponse,
    MessageDetailResponse,
    MessageFolderItem,
    MessageMediaItem,
    MessageMerge,
    MessageResponse,
    MessageSearchCursorResponse,
    MessageSearchItem,
    MessageSplit,
    MessageSyncMediaItem,
    MessageSyncResponse,
    MessageTagItem,
    MessageUpdate,
)
from app.modules.message.service import (
    add_media_to_message_service,
    cleanup_orphan_tags,
    create_message_service,
    delete_message_service,
    link_media_to_message,
    merge_messages_service,
    remove_media_from_message_service,
    reorder_message_media,
    split_message_service,
    update_message_service,
)
from app.modules.repository.file_schemas import FileUploadResponse

router = APIRouter(prefix="/messages", tags=["messages"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Domain query functions replace the legacy in-router implementations above.
# Keeping these aliases during the staged migration preserves private imports while
# making all route execution use the isolated domain module.
_aggregate_tags = _domain_aggregate_tags
_aggregate_tags_raw = _domain_aggregate_tags_raw
_batch_media_items = _domain_batch_media_items
_build_detail_query = _domain_build_detail_query
_build_detail_response = _domain_build_detail_response
_build_message_query = _domain_build_message_query
_build_sync_response = _domain_build_sync_response
_folder_fields = _domain_folder_fields
_folder_items = _domain_folder_items
_media_items_for = _domain_media_items_for
_paginate = _domain_paginate


def _parse_cursor(cursor):
    try:
        return _domain_parse_cursor(cursor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


_sync_media_item = _domain_sync_media_item

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("", response_model=CursorResponse)
def get_messages(
    cursor: Optional[str] = Query(None, description="游标，ISO 格式的 created_at"),
    limit: int = Query(20, ge=1, le=100),
    collection_id: Optional[int] = None,
    issue_id: Optional[int] = None,
    starred: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """获取消息列表（游标分页）"""
    try:
        return query_messages(
            db,
            cursor=cursor,
            limit=limit,
            collection_id=collection_id,
            issue_id=issue_id,
            starred=starred,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/dates", response_model=MessageDatesResponse)
def get_message_dates(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    collection_id: Optional[int] = None,
    issue_id: Optional[int] = None,
    query_text: Optional[str] = Query(None),
    media_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取指定月份中有消息的日期及数量"""
    return message_dates(
        db,
        year=year,
        month=month,
        collection_id=collection_id,
        issue_id=issue_id,
        query_text=query_text,
        media_id=media_id,
        tag_id=tag_id,
    )


@router.get("/sync", response_model=List[MessageSyncResponse])
def sync_messages(db: Session = Depends(get_db)):
    """全量同步：返回所有消息的完整详情（含 media 元数据和 tag）"""
    return sync_all(db)


@router.get("/with-detail", response_model=MessageDetailCursorResponse)
def get_messages_with_detail(
    cursor: Optional[str] = Query(None, description="游标，ISO 格式的 created_at"),
    direction: Optional[str] = Query(
        None, description="分页方向: 'forward' 加载更新的消息（cursor 之后）"
    ),
    inclusive: bool = Query(
        False, description="是否包含 cursor 本身（用 <= / >= 而非 < / >），用于位置恢复"
    ),
    limit: int = Query(20, ge=1, le=100),
    collection_id: Optional[int] = None,
    issue_id: Optional[int] = None,
    query_text: Optional[str] = Query(None, description="搜索文本，匹配 message.text"),
    media_id: Optional[int] = Query(
        None, description="媒体 ID，查询包含该媒体的所有消息"
    ),
    tag_id: Optional[int] = Query(
        None, description="标签 ID，查询包含该标签的所有消息"
    ),
    starred: Optional[bool] = Query(None, description="是否收藏"),
    db: Session = Depends(get_db),
):
    """获取消息列表，含完整媒体详情（游标分页）"""

    if direction == "forward" and cursor:
        pivot = _parse_cursor(cursor)
        op = Message.created_at >= pivot if inclusive else Message.created_at > pivot
        query = _build_detail_query(
            db, collection_id, query_text, media_id, tag_id, starred, issue_id
        )
        query = query.filter(op).order_by(Message.created_at.asc())
        rows = query.limit(limit + 1).all()
        has_more = len(rows) > limit
        items = rows[:limit]

        base = _build_detail_query(
            db, collection_id, query_text, media_id, tag_id, starred, issue_id
        )
        has_more_before = base.filter(Message.created_at < pivot).first() is not None

        ids = [m.id for m in items]
        media_by_msg = _batch_media_items(db, ids) if ids else {}
        result = [
            _build_detail_response(db, msg, media_by_msg=media_by_msg) for msg in items
        ]
        return MessageDetailCursorResponse(
            items=result,
            next_cursor=items[-1].created_at.isoformat()
            if has_more and items
            else None,
            prev_cursor=items[0].created_at.isoformat() if items else None,
            has_more=has_more,
            has_more_before=has_more_before,
        )

    # 默认：向后（desc）分页
    cursor_time = _parse_cursor(cursor)
    query = _build_message_query(
        db,
        collection_id,
        query_text,
        media_id,
        tag_id,
        cursor_time,
        starred=starred,
        inclusive=inclusive,
        issue_id=issue_id,
    )
    items, has_more, next_cursor = _paginate(query, limit)

    ids = [m.id for m in items]
    media_by_msg = _batch_media_items(db, ids) if ids else {}
    result = [
        _build_detail_response(db, msg, media_by_msg=media_by_msg) for msg in items
    ]
    return MessageDetailCursorResponse(
        items=result, next_cursor=next_cursor, has_more=has_more
    )


@router.get("/search", response_model=MessageSearchCursorResponse)
def search_messages_fts(
    q: str = Query(
        ..., min_length=1, description="搜索关键词（FTS5），多词之间隐式 AND"
    ),
    collection_id: Optional[int] = Query(None),
    issue_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    starred: Optional[bool] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None, description="游标，格式 '{rank}|{id}'"),
    db: Session = Depends(get_db),
):
    """基于 FTS5 的全文检索，返回精简结果（snippet + 元数据）。"""
    try:
        return search_messages(
            db,
            query=q,
            collection_id=collection_id,
            issue_id=issue_id,
            tag_id=tag_id,
            starred=starred,
            limit=limit,
            cursor=cursor,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{message_id}", response_model=MessageDetailResponse)
def get_message_detail(
    message_id: int,
    db: Session = Depends(get_db),
):
    """获取单条消息详情"""
    try:
        return query_message_detail(db, message_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("", response_model=MessageSyncResponse, status_code=201)
def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
):
    """创建新消息"""
    if message_data.files:
        raise HTTPException(
            status_code=409,
            detail="Media must be uploaded through a folder-backed message",
        )
    db_message = create_message_service(
        db,
        text=message_data.text,
        collection_id=message_data.collection_id,
        files=message_data.files,
        tag_ids=message_data.tag_ids,
        issue_id=message_data.issue_id,
    )
    return _build_sync_response(db, db_message)


@router.post("/create-from-client", response_model=MessageSyncResponse, status_code=201)
def create_message_from_client(
    message_data: MessageCreateFromClient,
    db: Session = Depends(get_db),
):
    """客户端主导创建消息：接受客户端提供的 ID，幂等"""
    if message_data.files:
        raise HTTPException(
            status_code=409,
            detail="Media must be uploaded through a folder-backed message",
        )
    # 解析 created_at
    created_at = None
    if message_data.created_at:
        try:
            created_at = datetime.fromisoformat(message_data.created_at)
        except ValueError:
            pass

    db_message = create_message_service(
        db,
        text=message_data.text,
        collection_id=message_data.collection_id,
        files=[cf.file_path for cf in message_data.files],
        tag_ids=None,
        created_at=created_at,
        issue_id=message_data.issue_id,
        client_id=message_data.id,
        media_id_resolver=lambda i: message_data.files[i].id,
    )
    return _build_sync_response(db, db_message)


@router.patch("/{message_id}", response_model=MessageDetailResponse)
def update_message(
    message_id: int,
    update_data: MessageUpdate,
    db: Session = Depends(get_db),
):
    """更新消息：文字、collection、媒体顺序"""
    created_at = None
    if update_data.created_at is not None:
        try:
            created_at = datetime.fromisoformat(update_data.created_at)
        except ValueError:
            pass

    try:
        message = update_message_service(
            db,
            message_id=message_id,
            text=update_data.text,
            collection_id=update_data.collection_id,
            issue_id=update_data.issue_id,
            starred=update_data.starred,
            created_at=created_at,
            tag_ids=update_data.tag_ids,
            media_order=update_data.media_order,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    return _build_detail_response(db, message)


@router.post("/merge", response_model=MessageDetailResponse)
def merge_messages(
    merge_data: MessageMerge,
    db: Session = Depends(get_db),
):
    """合并多条消息：文本拼接、媒体合并到第一条消息，删除其余消息。"""
    try:
        target = merge_messages_service(db, merge_data.message_ids)
    except ValueError as e:
        msg = str(e)
        if "Folder-backed" in msg:
            raise HTTPException(status_code=409, detail=msg)
        if "不存在" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=422, detail=msg)

    if target is None:
        raise HTTPException(status_code=404, detail="部分消息不存在")

    return _build_detail_response(db, target, media_limit=None)


@router.post("/{message_id}/split", response_model=MessageDetailResponse)
def split_message(
    message_id: int,
    split_data: MessageSplit,
    db: Session = Depends(get_db),
):
    """拆分消息：将选中的媒体移动到新消息中，复制 text/collection/starred/tags。"""
    try:
        new_msg = split_message_service(
            db,
            source_message_id=message_id,
            new_message_id=split_data.new_message_id,
            new_text=split_data.text,
            media_ids=split_data.media_ids,
        )
    except ValueError as e:
        msg = str(e)
        if "Folder-backed" in msg:
            raise HTTPException(status_code=409, detail=msg)
        if "not found" in msg.lower() or "找不到" in msg:
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=422, detail=msg)

    if new_msg is None:
        raise HTTPException(status_code=404, detail="Message not found")

    return _build_detail_response(db, new_msg, media_limit=None)


@router.post("/{message_id}/media", response_model=MessageDetailResponse)
def add_media_to_message(
    message_id: int,
    file_paths: List[str],
    db: Session = Depends(get_db),
):
    """向已有消息添加媒体文件"""
    try:
        add_media_to_message_service(db, message_id, file_paths)
    except ValueError as e:
        if "Folder-backed" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))

    return get_detail_after_write(db, message_id)


@router.post("/{message_id}/files", response_model=FileUploadResponse, status_code=202)
async def upload_file_to_message(
    message_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Write a media file to the message's primary folder; catalog owns all links."""
    from app.modules.repository import catalog as repository_catalog
    from app.modules.repository.folder_message_service import (
        store_file_in_primary_folder,
    )

    try:
        repo_id, destination = store_file_in_primary_folder(
            db,
            message_id,
            file.filename or "",
            file.file,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    finally:
        await file.close()

    repository_catalog.rescan(repo_id)
    return FileUploadResponse(message="上传成功，等待媒体处理", path=destination)


@router.delete("/{message_id}/media/{media_id}", response_model=MessageDetailResponse)
def remove_media_from_message(
    message_id: int,
    media_id: int,
    db: Session = Depends(get_db),
):
    """从消息中移除媒体（仅解除关联，不删除文件）"""
    try:
        removed = remove_media_from_message_service(db, message_id, media_id)
    except ValueError as e:
        if "Folder-backed" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))

    if not removed:
        raise HTTPException(status_code=404, detail="Media not found in this message")

    return get_detail_after_write(db, message_id)


@router.delete("/{message_id}", status_code=204)
def delete_message(
    message_id: int,
    db: Session = Depends(get_db),
):
    """删除消息"""
    try:
        if not delete_message_service(db, message_id):
            raise HTTPException(status_code=404, detail="Message not found")
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
