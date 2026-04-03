package com.example.myapplication.data.service

import android.content.Context
import android.content.SharedPreferences
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

        // 1. Push outbox
        try {
            val pushResult = db.syncOutboxRepository.syncToServer()
            Log.d(TAG, "Push 同步完成: $pushResult")
        } catch (e: Exception) {
            Log.e(TAG, "Push 同步失败: ${e.message}")
            // Push 失败不阻止 pull
        }

        // 2. Pull incremental (or full)
        val lastSyncTime = prefs.getString(KEY_LAST_SYNC_TIME, null)
        val pullResult = if (lastSyncTime != null) {
            db.messageRepository.syncIncremental(lastSyncTime)
        } else {
            db.messageRepository.syncFromRemote()
        }

        return when (pullResult) {
            is SyncResult.NeedFullSync -> {
                Log.w(TAG, "增量同步返回 410，执行全量同步")
                when (val fullResult = db.messageRepository.syncFromRemote()) {
                    is SyncResult.Success -> {
                        saveServerTime(prefs)
                        Log.d(TAG, "全量同步完成: ${fullResult.totalAffected} 条")
                        Result.success()
                    }
                    is SyncResult.Error -> {
                        Log.e(TAG, "全量同步失败: ${fullResult.message}")
                        Result.retry()
                    }
                    else -> Result.retry()
                }
            }
            is SyncResult.Success -> {
                saveServerTime(prefs)
                Log.d(TAG, "增量同步完成: ${pullResult.totalAffected} 条")
                Result.success()
            }
            is SyncResult.Error -> {
                Log.e(TAG, "增量同步失败: ${pullResult.message}")
                Result.retry()
            }
        }
    }

    private fun saveServerTime(prefs: SharedPreferences) {
        // 记录当前时间作为下次增量同步的起点
        prefs.edit()
            .putString(KEY_LAST_SYNC_TIME, java.time.Instant.now().toString())
            .apply()
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
