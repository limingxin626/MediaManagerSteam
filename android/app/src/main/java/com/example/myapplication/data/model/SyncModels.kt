package com.example.myapplication.data.model

import com.example.myapplication.data.database.entities.Collection
import com.example.myapplication.data.database.entities.Person

/**
 * 对应后端的 Collection Pydantic Model(原 Actor)
 */
data class RemoteCollection(
    val id: Long,
    val name: String,
    val description: String? = null,
    val cover: String? = null
) {
    /**
     * 转换为本地 Collection 实体。
     * @param coverLocalPath 封面本地路径(同步下载成功后传入);为空则不设置封面。
     */
    fun toLocalCollection(coverLocalPath: String? = null): Collection {
        return Collection(
            id = id,
            name = name,
            description = description,
            coverPath = coverLocalPath,
        )
    }
}

/**
 * 对应后端的 Person Pydantic Model
 */
data class RemotePerson(
    val id: Long,
    val name: String,
    val description: String? = null,
    val cover: String? = null
) {
    fun toLocalPerson(coverLocalPath: String? = null): Person {
        return Person(
            id = id,
            name = name,
            description = description,
            coverPath = coverLocalPath,
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
        val serverTime: String? = null,
        val serverCursorId: Long? = null
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
    val collection_id: Long?,
    val collection_name: String?,
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
    val position: Int = 0,
    val video_media_id: Long? = null,
    val frame_ms: Int? = null,
    val start_ms: Int? = null,
    val end_ms: Int? = null,
    val created_at: String? = null,
    val updated_at: String? = null,
    val people: List<RemotePersonRef>? = null
)

/** media 快照里的人物引用(后端只发 {id, name}) */
data class RemotePersonRef(
    val id: Long,
    val name: String
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
    val next_cursor_id: Long? = null,
    val has_more: Boolean,
    val server_time: String
)

data class RemoteChangeItem(
    /** 实体类型：MESSAGE | COLLECTION | PERSON | MEDIA | TAG */
    val entity_type: String,
    val entity_id: Long,
    /** 操作类型：UPSERT | DELETE */
    val operation: String,
    val timestamp: String,
    val data: Map<String, Any?>?  // 完整实体快照（DELETE 时为 null）
)
