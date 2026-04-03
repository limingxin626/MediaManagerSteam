package com.example.myapplication.data.service

import android.content.Context
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean

/**
 * SSE 实时监听器
 *
 * 连接后端 GET /sync/events，收到变更通知后触发增量同步。
 * - 仅在前台 + WiFi 连接时运行（由调用方控制 [start]/[stop]）
 * - 内置 debounce（500ms），避免短时间内多次变更触发大量同步
 * - 断线后自动重连（指数退避，最长 30 秒）
 */
class SseListener(
    private val context: Context,
    private val onChangeDetected: () -> Unit
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var eventSource: EventSource? = null
    private val isRunning = AtomicBoolean(false)
    private var debounceJob: Job? = null
    private var retryDelay = BASE_RETRY_DELAY_MS

    private val okHttpClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.SECONDS)   // SSE 永久连接，不超时
        .build()

    fun start() {
        if (!isRunning.compareAndSet(false, true)) return
        retryDelay = BASE_RETRY_DELAY_MS
        connect()
        Log.d(TAG, "SSE 监听器已启动")
    }

    fun stop() {
        isRunning.set(false)
        eventSource?.cancel()
        eventSource = null
        debounceJob?.cancel()
        Log.d(TAG, "SSE 监听器已停止")
    }

    private fun connect() {
        if (!isRunning.get()) return

        val url = "${SyncConfig.BASE_URL}/sync/events"
        val request = Request.Builder().url(url).build()

        eventSource = EventSources.createFactory(okHttpClient)
            .newEventSource(request, object : EventSourceListener() {
                override fun onOpen(eventSource: EventSource, response: Response) {
                    Log.d(TAG, "SSE 连接已建立")
                    retryDelay = BASE_RETRY_DELAY_MS
                }

                override fun onEvent(
                    eventSource: EventSource,
                    id: String?,
                    type: String?,
                    data: String
                ) {
                    if (data.contains("\"type\":\"connected\"")) return
                    Log.d(TAG, "SSE 收到变更通知：$data")
                    triggerSyncDebounced()
                }

                override fun onClosed(eventSource: EventSource) {
                    Log.d(TAG, "SSE 连接已关闭")
                    scheduleReconnect()
                }

                override fun onFailure(
                    eventSource: EventSource,
                    t: Throwable?,
                    response: Response?
                ) {
                    Log.w(TAG, "SSE 连接失败: ${t?.message}")
                    scheduleReconnect()
                }
            })
    }

    private fun triggerSyncDebounced() {
        debounceJob?.cancel()
        debounceJob = scope.launch {
            delay(DEBOUNCE_MS)
            onChangeDetected()
        }
    }

    private fun scheduleReconnect() {
        if (!isRunning.get()) return
        scope.launch {
            Log.d(TAG, "SSE 将在 ${retryDelay}ms 后重连")
            delay(retryDelay)
            retryDelay = (retryDelay * 2).coerceAtMost(MAX_RETRY_DELAY_MS)
            connect()
        }
    }

    companion object {
        private const val TAG = "SseListener"
        private const val DEBOUNCE_MS = 500L
        private const val BASE_RETRY_DELAY_MS = 2_000L
        private const val MAX_RETRY_DELAY_MS = 30_000L
    }
}
