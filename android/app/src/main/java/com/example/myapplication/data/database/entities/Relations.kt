package com.example.myapplication.data.database.entities

import androidx.room.Embedded
import androidx.room.Junction
import androidx.room.Relation

/**
 * 消息及其附件媒体列表
 */
data class MessageWithMedia(
    @Embedded val message: Message,
    @Relation(
        parentColumn = "id",
        entityColumn = "id",
        associateBy = Junction(
            value = MessageMedia::class,
            parentColumn = "messageId",
            entityColumn = "mediaId"
        )
    )
    val mediaList: List<Media> = emptyList()
)

/**
 * 消息及其标签列表
 */
data class MessageWithTags(
    @Embedded val message: Message,
    @Relation(
        parentColumn = "id",
        entityColumn = "id",
        associateBy = Junction(
            value = MessageTag::class,
            parentColumn = "messageId",
            entityColumn = "tagId"
        )
    )
    val tags: List<Tag> = emptyList()
)

/**
 * 消息完整信息（含媒体、标签、演员）
 */
data class MessageWithDetails(
    @Embedded val message: Message,
    @Relation(
        parentColumn = "actorId",
        entityColumn = "id"
    )
    val actor: Actor? = null,
    @Relation(
        parentColumn = "id",
        entityColumn = "id",
        associateBy = Junction(
            value = MessageMedia::class,
            parentColumn = "messageId",
            entityColumn = "mediaId"
        )
    )
    val mediaList: List<Media> = emptyList(),
    @Relation(
        parentColumn = "id",
        entityColumn = "id",
        associateBy = Junction(
            value = MessageTag::class,
            parentColumn = "messageId",
            entityColumn = "tagId"
        )
    )
    val tagList: List<Tag> = emptyList()
)

/**
 * 演员及其消息列表
 */
data class ActorWithMessages(
    @Embedded val actor: Actor,
    @Relation(
        parentColumn = "id",
        entityColumn = "actorId"
    )
    val messages: List<Message> = emptyList()
)
