package com.example.myapplication.data.service

import android.content.Context
import android.content.SharedPreferences
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * 缩略图显示模式：MOSAIC = Telegram 风格动态马赛克;GRID = 等分正方形网格(按数量 2/3 列)。
 */
enum class ThumbnailDisplayMode {
    MOSAIC,
    GRID;

    companion object {
        fun fromName(name: String?): ThumbnailDisplayMode =
            entries.firstOrNull { it.name == name } ?: MOSAIC
    }
}

/**
 * 同步相关偏好设置：增量游标 + 消息列表滚动锚点 + 缩略图显示模式。
 */
class SyncPreferences(context: Context) {

    private val prefs: SharedPreferences =
        context.applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

    private val _thumbnailMode = MutableStateFlow(
        ThumbnailDisplayMode.fromName(prefs.getString(KEY_THUMB_MODE, null))
    )
    /** 缩略图显示模式，供 Feed 实时观察。 */
    val thumbnailMode: StateFlow<ThumbnailDisplayMode> = _thumbnailMode

    fun setThumbnailMode(mode: ThumbnailDisplayMode) {
        prefs.edit().putString(KEY_THUMB_MODE, mode.name).apply()
        _thumbnailMode.value = mode
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

    /**
     * 增量同步游标 (server_time, since_id)。
     * 为空表示尚未做过全量初始化 —— 增量同步应提示用户先「初始化」。
     */
    fun getSyncCursor(): Pair<String, Long>? {
        val time = prefs.getString(KEY_LAST_SYNC_TIME, null) ?: return null
        return time to prefs.getLong(KEY_LAST_SYNC_ID, 0L)
    }

    fun setSyncCursor(serverTime: String, sinceId: Long) {
        prefs.edit()
            .putString(KEY_LAST_SYNC_TIME, serverTime)
            .putLong(KEY_LAST_SYNC_ID, sinceId)
            .apply()
    }

    fun clearSyncCursor() {
        prefs.edit()
            .remove(KEY_LAST_SYNC_TIME)
            .remove(KEY_LAST_SYNC_ID)
            .apply()
    }

    companion object {
        private const val PREFS_NAME = "sync_preferences"
        private const val KEY_MSG_SCROLL_ID = "message_scroll_anchor_id"
        private const val KEY_MSG_SCROLL_OFFSET = "message_scroll_anchor_offset"
        private const val KEY_LAST_SYNC_TIME = "last_sync_time"
        private const val KEY_LAST_SYNC_ID = "last_sync_id"
        private const val KEY_THUMB_MODE = "thumbnail_display_mode"
    }
}
