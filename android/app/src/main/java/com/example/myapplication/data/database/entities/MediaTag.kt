package com.example.myapplication.data.database.entities

import androidx.room.*

/**
 * 媒体-标签关联表
 * 实现多对多关系
 */
@Entity(
    tableName = "media_tags",
    primaryKeys = ["mediaId", "tagId"],
    foreignKeys = [
        ForeignKey(
            entity = Media::class,
            parentColumns = ["id"],
            childColumns = ["mediaId"],
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
        Index(value = ["mediaId"]),
        Index(value = ["tagId"])
    ]
)
data class MediaTag(
    val mediaId: Long,
    val tagId: Long
)
