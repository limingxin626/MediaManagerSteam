package com.example.myapplication.data.service

import com.example.myapplication.data.model.RemoteMediaItem
import com.example.myapplication.data.model.RemoteTagItem
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.POST

/**
 * 远程同步通用工具
 */
object SyncNetwork {

    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(ensureTrailingSlash(SyncConfig.BASE_URL))
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    val syncService: SyncService by lazy {
        retrofit.create(SyncService::class.java)
    }

    val pushService: SyncPushService by lazy {
        retrofit.create(SyncPushService::class.java)
    }

    val uploadService: MediaUploadService by lazy {
        retrofit.create(MediaUploadService::class.java)
    }

    val messageSyncService: MessageSyncService by lazy {
        retrofit.create(MessageSyncService::class.java)
    }

    private fun ensureTrailingSlash(baseUrl: String): String {
        return if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
    }
}

interface MessageSyncService {
    @POST("messages/create-from-client")
    suspend fun createFromClient(@Body request: MessageSyncRequest): MessageSyncResponse
}

data class ClientMediaFile(
    val id: Long,
    val file_path: String
)

data class MessageSyncRequest(
    val id: Long,
    val text: String?,
    val actor_id: Long?,
    val created_at: String?,
    val files: List<ClientMediaFile>
)

data class MessageSyncResponse(
    val id: Long,
    val media_items: List<RemoteMediaItem>,
    val tags: List<RemoteTagItem>
)

/**
 * 将相对路径拼成完整 URL。
 * - 若 path 已是 http(s) URL，则原样返回
 * - 若 path 为空，则返回空字符串
 */
fun buildFullUrl(baseUrl: String, path: String): String {
    val trimmed = path.trim()
    if (trimmed.isEmpty()) return ""
    if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) return trimmed

    val cleanBaseUrl = baseUrl.trimEnd('/')
    val cleanPath = if (trimmed.startsWith("/")) trimmed else "/$trimmed"
    return "$cleanBaseUrl$cleanPath"
}
