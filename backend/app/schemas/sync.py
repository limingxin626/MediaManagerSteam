from pydantic import BaseModel
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# GET /sync/changes 响应
# ---------------------------------------------------------------------------

class SyncChangeItem(BaseModel):
    entity_type: str
    entity_id: int
    operation: str       # UPSERT | DELETE
    timestamp: str
    data: Optional[Dict[str, Any]] = None  # UPSERT 时为完整实体快照，DELETE 时为 None


class SyncChangesResponse(BaseModel):
    changes: List[SyncChangeItem]
    next_cursor: Optional[str] = None
    next_cursor_id: Optional[int] = None  # 复合游标第二维：最后一条 SyncLog.id
    has_more: bool
    server_time: str


# ---------------------------------------------------------------------------
# POST /api/sync/apply 请求 / 响应
# ---------------------------------------------------------------------------

class SyncApplyItem(BaseModel):
    entityType: str       # ACTOR | MEDIA | MESSAGE | TAG
    operation: str        # UPSERT | DELETE
    entityId: int
    payload: Optional[Dict[str, Any]] = None


class SyncApplyRequest(BaseModel):
    changes: List[SyncApplyItem]


class SyncApplyResponse(BaseModel):
    applied: int = 0
    failed: int = 0
    message: Optional[str] = None
