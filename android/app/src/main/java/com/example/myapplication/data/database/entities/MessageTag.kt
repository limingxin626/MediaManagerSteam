package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index

/**
 * 消息标签关联实体类
 * 对应后端的message_tag表
 */
@Entity(
    tableName = "message_tag",
    primaryKeys = ["messageId", "tagId"],
    foreignKeys = [
        ForeignKey(
            entity = Message::class,
            parentColumns = ["id"],
            childColumns = ["messageId"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = Tag::class,
            parentColumns = ["id"],
            childColumns = ["tagId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["messageId"]),
        Index(value = ["tagId"])
    ]
)
data class MessageTag(
    val messageId: Long,
    val tagId: Long
)
