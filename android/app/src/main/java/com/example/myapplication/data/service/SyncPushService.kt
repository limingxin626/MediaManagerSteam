package com.example.myapplication.data.service

import com.google.gson.JsonElement
import retrofit2.http.Body
import retrofit2.http.POST

/**
 * 推送本地离线变更到服务器的接口。
 * 注意：此接口需要后端支持（建议实现一个批量 apply endpoint）。
 */
interface SyncPushService {

    @POST("api/sync/apply")
    suspend fun applyChanges(@Body request: ApplySyncChangesRequest): ApplySyncChangesResponse
}

data class ApplySyncChangesRequest(
    val changes: List<SyncChangeRequest>
)

data class SyncChangeRequest(
    val entityType: String,
    val operation: String,
    val entityId: Long,
    val payload: JsonElement? = null
)

data class ApplySyncChangesResponse(
    val applied: Int = 0,
    val failed: Int = 0,
    val message: String? = null
)
