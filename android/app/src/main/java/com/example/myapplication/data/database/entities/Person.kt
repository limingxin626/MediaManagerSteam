package com.example.myapplication.data.database.entities

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * 人物实体类
 * 对应后端的 Person 模型(照片人物,通过 media_person 与 Media 多对多)
 */
@Entity(
    tableName = "people",
    indices = [
        Index(value = ["name"])
    ]
)
data class Person(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,

    val name: String,                    // 人物姓名
    val description: String? = null,     // 人物描述
    val coverPath: String? = null,       // 封面路径
    val createdAt: Long = System.currentTimeMillis(),        // 创建时间
    val updatedAt: Long = System.currentTimeMillis()         // 更新时间
)
