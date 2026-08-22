package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index

@Entity(
    tableName = "system_media_tag",
    primaryKeys = ["systemMediaKey", "tagId"],
    foreignKeys = [
        ForeignKey(
            entity = SystemMediaMetadata::class,
            parentColumns = ["stableKey"],
            childColumns = ["systemMediaKey"],
            onDelete = ForeignKey.CASCADE
        ),
        ForeignKey(
            entity = Tag::class,
            parentColumns = ["id"],
            childColumns = ["tagId"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index("systemMediaKey"), Index("tagId")]
)
data class SystemMediaTag(
    val systemMediaKey: String,
    val tagId: Long
)
