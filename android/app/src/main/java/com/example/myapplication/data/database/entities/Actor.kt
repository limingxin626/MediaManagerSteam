package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 演员实体类
 * 对应后端的Actor模型
 */
@Entity(
    tableName = "actors",
    indices = [
        Index(value = ["name"])
    ]
)
data class Actor(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val name: String,                    // 演员姓名
    val description: String? = null,     // 演员描述
    val avatarPath: String? = null,      // 头像路径
    val createdAt: Long = System.currentTimeMillis(),        // 创建时间
    val updatedAt: Long = System.currentTimeMillis()         // 更新时间
)