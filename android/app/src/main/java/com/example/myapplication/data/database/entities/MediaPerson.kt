package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index

/**
 * 媒体-人物关联表
 * 实现多对多关系(对应后端 media_person)
 */
@Entity(
    tableName = "media_people",
    primaryKeys = ["mediaId", "personId"],
    foreignKeys = [
        ForeignKey(
            entity = Media::class,
            parentColumns = ["id"],
            childColumns = ["mediaId"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = Person::class,
            parentColumns = ["id"],
            childColumns = ["personId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [
        Index(value = ["mediaId"]),
        Index(value = ["personId"])
    ]
)
data class MediaPerson(
    val mediaId: Long,
    val personId: Long
)
