package com.example.myapplication.data.service

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * 监听网络连接状态，只关心 WiFi（局域网同步场景）。
 * 暴露 [isWifiConnected] StateFlow，ViewModel / Worker 可订阅。
 */
class NetworkMonitor(context: Context) {

    private val connectivityManager =
        context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager

    private val _isWifiConnected = MutableStateFlow(checkWifi())
    val isWifiConnected: StateFlow<Boolean> = _isWifiConnected.asStateFlow()

    private val networkCallback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            _isWifiConnected.value = checkWifi()
        }

        override fun onLost(network: Network) {
            _isWifiConnected.value = checkWifi()
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
    }

    private fun checkWifi(): Boolean {
        val active = connectivityManager.activeNetwork ?: return false
        val caps = connectivityManager.getNetworkCapabilities(active) ?: return false
        return caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)
    }

    fun unregister() {
        connectivityManager.unregisterNetworkCallback(networkCallback)
    }
}
