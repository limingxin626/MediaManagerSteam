package com.example.myapplication.data.database

import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import android.content.Context
import com.example.myapplication.data.database.dao.ActorDao
import com.example.myapplication.data.database.dao.MediaDao
import com.example.myapplication.data.database.dao.TagDao
import com.example.myapplication.data.database.dao.SyncOutboxDao
import com.example.myapplication.data.database.dao.MessageDao
import com.example.myapplication.data.database.entities.Actor
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.data.database.entities.SyncOutboxItem
import com.example.myapplication.data.database.entities.Message
import com.example.myapplication.data.database.entities.MessageMedia
import com.example.myapplication.data.database.entities.MessageTag
import com.example.myapplication.data.database.entities.MediaTag

/**
 * 应用主数据库
 */
@Database(
    entities = [
        Actor::class,
        Media::class,
        Tag::class,
        SyncOutboxItem::class,
        Message::class,
        MessageMedia::class,
        MessageTag::class,
        MediaTag::class
    ],
    version = 29,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    
    // DAO 访问接口
    abstract fun actorDao(): ActorDao
    abstract fun mediaDao(): MediaDao
    abstract fun tagDao(): TagDao
    abstract fun syncOutboxDao(): SyncOutboxDao
    abstract fun messageDao(): MessageDao
    
    companion object {
        // 数据库名称
        const val DATABASE_NAME = "media_management_database"
        
        // 单例模式
        @Volatile
        private var INSTANCE: AppDatabase? = null
        
        /**
         * 获取数据库实例
         */
        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    DATABASE_NAME
                )
                .addMigrations(*DatabaseMigrations.ALL_MIGRATIONS)
                .fallbackToDestructiveMigration()
                .build()
                
                INSTANCE = instance
                instance
            }
        }
    }
}