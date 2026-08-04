package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 合集实体类
 * 对应后端的 Collection 模型(原 Actor)
 */
@Entity(
    tableName = "collections",
    indices = [
        Index(value = ["name"])
    ]
)
data class Collection(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val name: String,                    // 合集名称
    val description: String? = null,     // 合集描述
    val coverPath: String? = null,       // 封面路径
    val createdAt: Long = System.currentTimeMillis(),        // 创建时间
    val updatedAt: Long = System.currentTimeMillis()         // 更新时间
)
