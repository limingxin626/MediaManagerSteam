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

    fun getMessageScrollAnchor(): Pair<Long, Int>? {
        val id = prefs.getLong(KEY_MSG_SCROLL_ID, -1L)
        if (id <= 0L) return null
        val offset = prefs.getInt(KEY_MSG_SCROLL_OFFSET, 0)
        return id to offset
    }

    fun setMessageScrollAnchor(messageId: Long, offsetPx: Int) {
        prefs.edit()
            .putLong(KEY_MSG_SCROLL_ID, messageId)
            .putInt(KEY_MSG_SCROLL_OFFSET, offsetPx)
            .apply()
    }

    fun clearMessageScrollAnchor() {
        prefs.edit()
            .remove(KEY_MSG_SCROLL_ID)
            .remove(KEY_MSG_SCROLL_OFFSET)
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "sync_preferences"
        private const val KEY_OFFLINE_MODE = "offline_mode"
        private const val KEY_MSG_SCROLL_ID = "message_scroll_anchor_id"
        private const val KEY_MSG_SCROLL_OFFSET = "message_scroll_anchor_offset"
    }
}
