package com.example.myapplication.data


import android.content.Context
import com.example.myapplication.data.database.AppDatabase
import com.example.myapplication.data.repository.CollectionRepository
import com.example.myapplication.data.repository.MediaRepository
import com.example.myapplication.data.repository.MessageRepository
import com.example.myapplication.data.repository.PersonRepository
import com.example.myapplication.data.repository.SyncOutboxRepository
import com.example.myapplication.data.repository.TagRepository
import com.example.myapplication.data.repository.SystemMediaMetadataRepository
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
    private val collectionDao = database.collectionDao()
    private val personDao = database.personDao()
    private val mediaDao = database.mediaDao()
    private val tagDao = database.tagDao()
    private val syncOutboxDao = database.syncOutboxDao()
    private val messageDao = database.messageDao()
    private val systemMediaMetadataDao = database.systemMediaMetadataDao()

    // 同步偏好
    val syncPreferences = SyncPreferences(appContext)

    // Repository实例
    val syncOutboxRepository = SyncOutboxRepository(syncOutboxDao)

    val collectionRepository = CollectionRepository(collectionDao, syncOutboxRepository)
    val personRepository = PersonRepository(personDao, syncOutboxRepository)
    val mediaRepository = MediaRepository(mediaDao, syncOutboxRepository)
    val tagRepository = TagRepository(tagDao)
    val systemMediaMetadataRepository = SystemMediaMetadataRepository(systemMediaMetadataDao)
    val messageRepository =
        MessageRepository(messageDao, mediaDao, tagDao, collectionDao, personDao, syncOutboxRepository, database)

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
