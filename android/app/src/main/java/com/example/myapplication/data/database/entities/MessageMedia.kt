package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index

/**
 * 消息媒体关联实体类
 * 对应后端的MessageMedia模型
 */
@Entity(
    tableName = "message_media",
    primaryKeys = ["messageId", "mediaId"],
    foreignKeys = [
        ForeignKey(
            entity = Message::class,
            parentColumns = ["id"],
            childColumns = ["messageId"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = Media::class,
            parentColumns = ["id"],
            childColumns = ["mediaId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["messageId"]),
        Index(value = ["mediaId"])
    ]
)
data class MessageMedia(
    val messageId: Long,
    val mediaId: Long,
    val position: Int,
    val createdAt: Long = System.currentTimeMillis()
)
