package com.example.myapplication.ui.model

import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.data.model.SystemMedia

data class SystemMediaWithMetadata(
    val media: SystemMedia,
    val starred: Boolean = false,
    val tags: List<Tag> = emptyList()
)

fun matchesSystemMediaMetadata(
    starred: Boolean,
    tagIds: Collection<Long>,
    starredOnly: Boolean,
    selectedTagId: Long?
): Boolean = (!starredOnly || starred) &&
    (selectedTagId == null || selectedTagId in tagIds)

fun filterSystemMedia(
    items: List<SystemMediaWithMetadata>,
    starredOnly: Boolean,
    tagId: Long?
): List<SystemMediaWithMetadata> = items.filter { item ->
    matchesSystemMediaMetadata(
        starred = item.starred,
        tagIds = item.tags.map { it.id },
        starredOnly = starredOnly,
        selectedTagId = tagId
    )
}

fun updateSystemMediaSelection(
    selectedKeys: Set<String>,
    key: String,
    selected: Boolean
): Set<String> = if (selected) selectedKeys + key else selectedKeys - key

fun orderedSelectedSystemMedia(
    items: List<SystemMediaWithMetadata>,
    selectedKeys: Set<String>
): List<SystemMedia> = items.map { it.media }.filter { it.stableKey in selectedKeys }
