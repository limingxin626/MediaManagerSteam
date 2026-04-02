package com.example.myapplication.data.repository

import android.util.Log
import com.example.myapplication.data.database.dao.SyncOutboxDao
import com.example.myapplication.data.database.entities.SyncOutboxItem
import com.example.myapplication.data.model.PushSyncResult
import com.example.myapplication.data.service.ApplySyncChangesRequest
import com.example.myapplication.data.service.SyncChangeRequest
import com.example.myapplication.data.service.SyncNetwork
import com.google.gson.JsonParser

class SyncOutboxRepository(
    private val dao: SyncOutboxDao
) {

    suspend fun enqueueUpsert(entityType: String, entityId: Long, payloadJson: String) {
        // 同一个实体的 PENDING UPSERT 只保留最新一条，避免重复推送
        dao.deletePendingSameKey(
            entityType = entityType,
            operation = SyncOutboxItem.OP_UPSERT,
            entityId = entityId
        )

        dao.insert(
            SyncOutboxItem(
                entityType = entityType,
                operation = SyncOutboxItem.OP_UPSERT,
                entityId = entityId,
                payloadJson = payloadJson
            )
        )
    }

    suspend fun enqueueDelete(entityType: String, entityId: Long) {
        // 删除优先：移除同实体待推送的 UPSERT，避免先 upsert 再 delete
        dao.deletePendingSameKey(
            entityType = entityType,
            operation = SyncOutboxItem.OP_UPSERT,
            entityId = entityId
        )
        dao.deletePendingSameKey(
            entityType = entityType,
            operation = SyncOutboxItem.OP_DELETE,
            entityId = entityId
        )

        dao.insert(
            SyncOutboxItem(
                entityType = entityType,
                operation = SyncOutboxItem.OP_DELETE,
                entityId = entityId,
                payloadJson = null
            )
        )
    }

    suspend fun syncToServer(limit: Int = 200): PushSyncResult {
        return try {
            val pending = dao.getByStatus(SyncOutboxItem.STATUS_PENDING, limit)
            if (pending.isEmpty()) {
                return PushSyncResult.Success(pushedCount = 0, skippedCount = 0)
            }

            val changes = pending.map { item ->
                val payload = item.payloadJson?.let {
                    try {
                        JsonParser.parseString(it)
                    } catch (_: Exception) {
                        null
                    }
                }

                SyncChangeRequest(
                    entityType = item.entityType,
                    operation = item.operation,
                    entityId = item.entityId,
                    payload = payload
                )
            }

            val response = SyncNetwork.pushService.applyChanges(ApplySyncChangesRequest(changes))

            // 简化处理：只要服务端返回成功，就认为本批全部成功并清除
            pending.forEach { dao.updateStatus(it.id, SyncOutboxItem.STATUS_DONE) }
            dao.deleteByStatus(SyncOutboxItem.STATUS_DONE)

            PushSyncResult.Success(pushedCount = response.applied.coerceAtLeast(pending.size))
        } catch (e: Exception) {
            Log.e(TAG, "syncToServer failed: ${e.message}", e)

            // 标记尝试次数，保留队列以便下次重试
            val pending = dao.getByStatus(SyncOutboxItem.STATUS_PENDING, limit)
            pending.forEach { dao.markAttempt(it.id, e.message) }

            PushSyncResult.Error(message = e.message ?: "未知错误", pushedCount = 0, failedCount = pending.size)
        }
    }

    companion object {
        private const val TAG = "SyncOutboxRepository"
    }
}
