package com.example.myapplication.data.model

/**
 * 消息排序方式
 */
enum class MessageSortBy(val displayName: String) {
    CREATED_DESC("最新创建"),
    CREATED_ASC("最早创建"),
    STARRED_FIRST("收藏优先");
}
