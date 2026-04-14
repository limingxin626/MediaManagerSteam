package com.example.myapplication.data.service

import android.content.Context
import android.content.SharedPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * 同步相关偏好设置。
 * [isOfflineMode]：手动离线模式开关，开启后跳过所有即时同步和 WorkManager 后台同步。
 */
class SyncPreferences(context: Context) {

    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private val _isOfflineMode = MutableStateFlow(prefs.getBoolean(KEY_OFFLINE_MODE, false))
    val isOfflineMode: StateFlow<Boolean> = _isOfflineMode.asStateFlow()

    fun setOfflineMode(enabled: Boolean) {
        prefs.edit().putBoolean(KEY_OFFLINE_MODE, enabled).apply()
        _isOfflineMode.value = enabled
    }

    companion object {
        private const val PREFS_NAME = "sync_preferences"
        private const val KEY_OFFLINE_MODE = "offline_mode"
    }
}
