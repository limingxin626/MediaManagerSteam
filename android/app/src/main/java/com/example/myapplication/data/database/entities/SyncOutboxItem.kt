package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 离线同步 Outbox：记录本地对数据的变更，待联网后推送到服务器。
 */
@Entity(
    tableName = "sync_outbox",
    indices = [
        Index(value = ["status"]),
        Index(value = ["entityType", "operation", "entityId"])
    ]
)
data class SyncOutboxItem(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val entityType: String,
    val operation: String,
    val entityId: Long,
    val payloadJson: String? = null,
    val status: String = STATUS_PENDING,
    val attemptCount: Int = 0,
    val lastError: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis()
) {
    companion object {
        const val STATUS_PENDING = "PENDING"
        const val STATUS_DONE = "DONE"
        const val STATUS_FAILED = "FAILED"

        const val OP_UPSERT = "UPSERT"
        const val OP_DELETE = "DELETE"

        const val ENTITY_ACTOR = "ACTOR"
        const val ENTITY_MEDIA = "MEDIA"
        const val ENTITY_MESSAGE = "MESSAGE"
        const val ENTITY_TAG = "TAG"
    }
}
