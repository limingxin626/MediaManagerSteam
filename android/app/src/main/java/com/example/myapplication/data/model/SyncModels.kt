package com.example.myapplication.data.model

import com.example.myapplication.data.database.entities.Actor

/**
 * 对应后端的 Actor Pydantic Model
 */
data class RemoteActor(
    val id: Long,
    val name: String,
    val description: String? = null,
    val avatar: String? = null
) {
    /**
     * 转换为本地 Actor 实体。
     * @param avatarLocalPath 头像本地路径（同步下载成功后传入）；为空则不设置头像。
     */
    fun toLocalActor(avatarLocalPath: String? = null): Actor {
        return Actor(
            id = id,
            name = name,
            description = description,
            avatarPath = avatarLocalPath,
        )
    }
}

/**
 * 同步结果封装
 */
sealed class SyncResult {
    data class Success(
        val insertedCount: Int,
        val updatedCount: Int,
        val deletedCount: Int = 0,
        val serverTime: String? = null
    ) : SyncResult() {
        val totalAffected: Int get() = insertedCount + updatedCount + deletedCount
    }

    data class Error(val message: String) : SyncResult()

    /** 增量同步返回 410：需要全量同步 */
    object NeedFullSync : SyncResult()
}

/**
 * 对应后端 MessageSyncResponse
 */
data class RemoteMessage(
    val id: Long,
    val text: String?,
    val actor_id: Long?,
    val actor_name: String?,
    val starred: Boolean,
    val created_at: String,
    val updated_at: String,
    val media_items: List<RemoteMediaItem>,
    val tags: List<RemoteTagItem>
)

data class RemoteMediaItem(
    val id: Long,
    val file_url: String,
    val file_hash: String?,
    val file_size: Long?,
    val mime_type: String?,
    val width: Int?,
    val height: Int?,
    val duration_ms: Int?,
    val rating: Int,
    val starred: Boolean,
    val thumb_url: String,
    val position: Int
)

data class RemoteTagItem(
    val id: Long,
    val name: String,
    val category: String?
)

/**
 * 对应后端 GET /sync/changes 响应
 */
data class RemoteChangesResponse(
    val changes: List<RemoteChangeItem>,
    val next_cursor: String?,
    val has_more: Boolean,
    val server_time: String
)

data class RemoteChangeItem(
    val entity_type: String,
    val entity_id: Long,
    val operation: String,   // UPSERT | DELETE
    val timestamp: String,
    val data: Map<String, Any?>?  // 完整实体快照（DELETE 时为 null）
)
