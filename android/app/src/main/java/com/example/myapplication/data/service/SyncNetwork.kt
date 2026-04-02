package com.example.myapplication.data.service

import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

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

    private fun ensureTrailingSlash(baseUrl: String): String {
        return if (baseUrl.endsWith("/")) baseUrl else "$baseUrl/"
    }
}

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
