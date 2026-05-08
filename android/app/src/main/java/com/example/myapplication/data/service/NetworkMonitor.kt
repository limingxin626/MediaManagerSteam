package com.example.myapplication.data.service

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.util.Log
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.concurrent.TimeUnit

/**
 * 监听网络状态 + 后端可达性。
 * - [isWifiConnected]：系统层 WiFi 连接状态
 * - [isBackendReachable]：周期性 GET /health 的结果
 * - [isOnline]：手动离线模式 OFF + 后端可达 = 真正可同步
 */
class NetworkMonitor(
    context: Context,
    private val syncPreferences: SyncPreferences,
) {
    private val TAG = "NetworkMonitor"

    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private val healthClient = OkHttpClient.Builder()
        .connectTimeout(HEALTH_TIMEOUT_SEC, TimeUnit.SECONDS)
        .readTimeout(HEALTH_TIMEOUT_SEC, TimeUnit.SECONDS)
        .callTimeout(HEALTH_TIMEOUT_SEC, TimeUnit.SECONDS)
        .build()

    private val _isWifiConnected = MutableStateFlow(checkWifi())
    val isWifiConnected: StateFlow<Boolean> = _isWifiConnected.asStateFlow()

    private val _isBackendReachable = MutableStateFlow(false)
    val isBackendReachable: StateFlow<Boolean> = _isBackendReachable.asStateFlow()

    val isOnline: StateFlow<Boolean> = combine(
        syncPreferences.isOfflineMode,
        _isBackendReachable,
    ) { offline, reachable -> !offline && reachable }
        .stateIn(scope, SharingStarted.Eagerly, false)

    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            _isWifiConnected.value = checkWifi()
            scope.launch { probeOnce() }
        }

        override fun onLost(network: Network) {
            _isWifiConnected.value = checkWifi()
            _isBackendReachable.value = false
        }

        override fun onCapabilitiesChanged(network: Network, caps: NetworkCapabilities) {
            _isWifiConnected.value = caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
        }
    }

    init {
        val request = NetworkRequest.Builder()
            .addTransportType(NetworkCapabilities.TRANSPORT_WIFI)
            .build()
        connectivityManager.registerNetworkCallback(request, networkCallback)
        scope.launch { healthLoop() }
    }

    private suspend fun healthLoop() {
        while (true) {
            probeOnce()
            delay(HEALTH_INTERVAL_MS)
        }
    }

    /** 主动触发一次探活，供 App 启动 / 用户手动重试时调用。 */
    fun probeNow() {
        scope.launch { probeOnce() }
    }

    private suspend fun probeOnce() {
        // 未连任何网络时直接判定不可达，避免无谓 socket 失败
        if (connectivityManager.activeNetwork == null) {
            _isBackendReachable.value = false
            return
        }
        val reachable = withContext(Dispatchers.IO) {
            try {
                val req = Request.Builder()
                    .url("${SyncConfig.BASE_URL}/health")
                    .get()
                    .build()
                healthClient.newCall(req).execute().use { it.isSuccessful }
            } catch (e: Exception) {
                Log.d(TAG, "health probe failed: ${e.message}")
                false
            }
        }
        if (_isBackendReachable.value != reachable) {
            Log.i(TAG, "backend reachable: ${_isBackendReachable.value} -> $reachable")
        }
        _isBackendReachable.value = reachable
    }

    private fun checkWifi(): Boolean {
        val active = connectivityManager.activeNetwork ?: return false
        val caps = connectivityManager.getNetworkCapabilities(active) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }

    fun unregister() {
        connectivityManager.unregisterNetworkCallback(networkCallback)
    }

    companion object {
        private const val HEALTH_INTERVAL_MS = 30_000L
        private const val HEALTH_TIMEOUT_SEC = 3L
    }
}
