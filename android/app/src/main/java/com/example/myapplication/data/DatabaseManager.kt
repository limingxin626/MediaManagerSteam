package com.example.myapplication.data


import android.content.Context
import com.example.myapplication.data.database.AppDatabase
import com.example.myapplication.data.repository.ActorRepository
import com.example.myapplication.data.repository.MediaRepository
import com.example.myapplication.data.repository.MessageRepository
import com.example.myapplication.data.repository.SyncOutboxRepository
import com.example.myapplication.data.repository.TagRepository
import com.example.myapplication.data.service.NetworkMonitor
import com.example.myapplication.data.service.SyncPreferences

/**
 * 数据库管理器
 * 简单的单例模式，用于管理数据库和仓库实例
 */
class DatabaseManager private constructor(context: Context) {

    // 应用上下文（用于同步等需要 Context 的操作）
    val appContext: Context = context.applicationContext

    // 数据库实例
    private val database = AppDatabase.getDatabase(context)

    // DAO实例
    private val actorDao = database.actorDao()
    private val mediaDao = database.mediaDao()
    private val tagDao = database.tagDao()
    private val syncOutboxDao = database.syncOutboxDao()
    private val messageDao = database.messageDao()

    // 网络监听
    val networkMonitor = NetworkMonitor(appContext)

    // 同步偏好
    val syncPreferences = SyncPreferences(appContext)

    // Repository实例
    val syncOutboxRepository = SyncOutboxRepository(syncOutboxDao, networkMonitor, syncPreferences)

    val actorRepository = ActorRepository(actorDao, syncOutboxRepository)
    val mediaRepository = MediaRepository(mediaDao, syncOutboxRepository)
    val tagRepository = TagRepository(tagDao)
    val messageRepository =
        MessageRepository(messageDao, mediaDao, tagDao, actorDao, syncOutboxRepository, database)

    companion object {
        @Volatile
        private var INSTANCE: DatabaseManager? = null

        fun getInstance(context: Context): DatabaseManager {
            return INSTANCE ?: synchronized(this) {
                val instance = DatabaseManager(context.applicationContext)
                INSTANCE = instance
                instance
            }
        }
    }
}
