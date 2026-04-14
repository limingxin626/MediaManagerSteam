package com.example.myapplication.data.service

import android.content.Context
import android.util.Log
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.model.SyncResult
import com.example.myapplication.data.service.SyncWorker.Companion.scheduleImmediateSync
import com.example.myapplication.data.service.SyncWorker.Companion.schedulePeriodicSync
import java.util.concurrent.TimeUnit

/**
 * 后台同步 Worker（WorkManager）
 *
 * 流程：push outbox → pull 增量变更（或全量回退）
 *
 * 注册两种任务：
 * 1. [schedulePeriodicSync] — 每 15 分钟一次（仅 WiFi）
 * 2. [scheduleImmediateSync] — 网络恢复时立即触发一次
 */
class SyncWorker(
    appContext: Context,
    params: WorkerParameters
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val db = DatabaseManager.getInstance(applicationContext)
        val prefs = applicationContext.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        // 离线模式下跳过所有同步
        if (db.syncPreferences.isOfflineMode.value) {
            Log.d(TAG, "离线模式已开启，跳过后台同步")
            return Result.success()
        }

        // 1. Push outbox
        try {
            val pushResult = db.syncOutboxRepository.syncToServer()
            Log.d(TAG, "Push 同步完成: $pushResult")
        } catch (e: Exception) {
            Log.e(TAG, "Push 同步失败: ${e.message}")
            // Push 失败不阻止 pull
        }

        // 2. Pull incremental（无 lastSyncTime 时跳过，需用户手动触发全量）
        val lastSyncTime = prefs.getString(KEY_LAST_SYNC_TIME, null)
        if (lastSyncTime == null) {
            Log.d(TAG, "无同步游标，跳过增量拉取（请在设置页手动执行全量同步）")
            return Result.success()
        }

        return when (val pullResult = db.messageRepository.syncIncremental(lastSyncTime)) {
            is SyncResult.NeedFullSync -> {
                // 410：游标过期，不自动全量，提示用户手动操作
                Log.w(TAG, "增量同步返回 410（游标已过期），请在设置页手动执行全量同步")
                prefs.edit().remove(KEY_LAST_SYNC_TIME).apply()
                Result.success()
            }

            is SyncResult.Success -> {
                val serverTime = pullResult.serverTime
                if (serverTime != null) {
                    prefs.edit().putString(KEY_LAST_SYNC_TIME, serverTime).apply()
                }
                Log.d(TAG, "增量同步完成: ${pullResult.totalAffected} 条")
                Result.success()
            }

            is SyncResult.Error -> {
                Log.e(TAG, "增量同步失败: ${pullResult.message}")
                Result.retry()
            }
        }
    }

    companion object {
        const val TAG = "SyncWorker"
        const val PREFS_NAME = "sync_prefs"
        const val KEY_LAST_SYNC_TIME = "last_sync_time"

        private const val PERIODIC_WORK_NAME = "periodic_sync"
        private const val IMMEDIATE_WORK_NAME = "immediate_sync"

        private val wifiConstraints = Constraints.Builder()
            .setRequiredNetworkType(NetworkType.UNMETERED)  // WiFi only
            .build()

        /** 调度定期同步（每 15 分钟，WiFi 下执行）*/
        fun schedulePeriodicSync(context: Context) {
            val request = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
                .setConstraints(wifiConstraints)
                .build()
            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                PERIODIC_WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                request
            )
            Log.d(TAG, "定期同步已调度（每 15 分钟）")
        }

        /** 网络恢复后立即触发一次同步 */
        fun scheduleImmediateSync(context: Context) {
            val request = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(wifiConstraints)
                .build()
            WorkManager.getInstance(context).enqueueUniqueWork(
                IMMEDIATE_WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                request
            )
            Log.d(TAG, "立即同步已调度")
        }
    }
}
