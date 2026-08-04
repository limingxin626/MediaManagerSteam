package com.example.myapplication.data.model

sealed class PushSyncResult {
    data class Success(
        val pushedCount: Int,
        val skippedCount: Int = 0
    ) : PushSyncResult()

    data class Error(
        val message: String,
        val pushedCount: Int = 0,
        val failedCount: Int = 0
    ) : PushSyncResult()
}
