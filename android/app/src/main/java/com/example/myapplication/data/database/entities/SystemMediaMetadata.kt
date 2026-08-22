package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "system_media_metadata")
data class SystemMediaMetadata(
    @PrimaryKey val stableKey: String,
    val contentUri: String,
    val starred: Boolean = false,
    val updatedAt: Long = System.currentTimeMillis()
)
