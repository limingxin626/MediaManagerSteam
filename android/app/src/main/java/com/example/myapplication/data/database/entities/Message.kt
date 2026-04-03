package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import androidx.room.ForeignKey
import androidx.room.Index

/**
 * 消息实体类
 * 对应后端的Message模型
 */
@Entity(
    tableName = "messages",
    foreignKeys = [
        ForeignKey(
            entity = Actor::class,
            parentColumns = ["id"],
            childColumns = ["actorId"],
            onDelete = ForeignKey.SET_NULL
        )
    ],
    indices = [
        Index(value = ["actorId"]),
        Index(value = ["createdAt"])
    ]
)
data class Message(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val text: String? = null,
    val actorId: Long? = null,
    val starred: Boolean = false,
    val source: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis(),
    val sendStatus: String = MSG_STATUS_SYNCED
) {
    companion object {
        const val MSG_STATUS_SYNCED  = "SYNCED"
        const val MSG_STATUS_PUSHING = "PUSHING"
        const val MSG_STATUS_PUSH_FAILED = "PUSH_FAILED"
    }
}
