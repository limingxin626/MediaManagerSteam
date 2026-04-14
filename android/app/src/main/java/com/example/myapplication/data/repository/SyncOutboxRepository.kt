package com.example.myapplication.data.repository

import android.util.Log
import com.example.myapplication.data.database.dao.SyncOutboxDao
import com.example.myapplication.data.database.entities.SyncOutboxItem
import com.example.myapplication.data.model.PushSyncResult
import com.example.myapplication.data.service.ApplySyncChangesRequest
import com.example.myapplication.data.service.SyncChangeRequest
import com.example.myapplication.data.service.SyncNetwork
import com.example.myapplication.data.service.NetworkMonitor
import com.example.myapplication.data.service.SyncPreferences
import com.google.gson.JsonParser

class SyncOutboxRepository(
    private val dao: SyncOutboxDao,
    private val networkMonitor: NetworkMonitor? = null,
    private val syncPreferences: SyncPreferences? = null
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
        // 手动离线模式时跳过
        if (syncPreferences?.isOfflineMode?.value == true) {
            Log.d(TAG, "syncToServer 跳过：已开启离线模式")
            return PushSyncResult.Skipped
        }

        // 无 WiFi 时跳过，由 WorkManager 在网络恢复后重试
        if (networkMonitor?.isWifiConnected?.value == false) {
            Log.d(TAG, "syncToServer 跳过：当前无 WiFi 连接")
            return PushSyncResult.Skipped
        }

        // 在 try 之前捕获 pending 列表，确保 catch 也能使用同一快照
        val pending = dao.getByStatus(SyncOutboxItem.STATUS_PENDING, limit)
        if (pending.isEmpty()) {
            return PushSyncResult.Success(pushedCount = 0, skippedCount = 0)
        }

        return try {
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

            // 使用同一快照标记尝试次数，超过上限的标记为 FAILED
            for (item in pending) {
                if (item.attemptCount + 1 >= MAX_RETRY_COUNT) {
                    dao.updateStatus(item.id, SyncOutboxItem.STATUS_FAILED)
                    Log.w(TAG, "Outbox item #${item.id} 超过最大重试次数 ($MAX_RETRY_COUNT)，标记为 FAILED")
                } else {
                    dao.markAttempt(item.id, e.message)
                }
            }

            PushSyncResult.Error(message = e.message ?: "未知错误", pushedCount = 0, failedCount = pending.size)
        }
    }

    companion object {
        private const val TAG = "SyncOutboxRepository"
        private const val MAX_RETRY_COUNT = 10
    }
}
