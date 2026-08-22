package com.example.myapplication.data.repository

import com.example.myapplication.data.database.dao.SystemMediaMetadataDao
import com.example.myapplication.data.database.entities.SystemMediaMetadata
import com.example.myapplication.data.database.entities.SystemMediaTag
import kotlinx.coroutines.flow.Flow

class SystemMediaMetadataRepository(
    private val dao: SystemMediaMetadataDao
) {
    val metadata: Flow<List<SystemMediaMetadata>> = dao.observeAllMetadata()
    val tagLinks: Flow<List<SystemMediaTag>> = dao.observeAllTagLinks()

    suspend fun toggleStarred(stableKey: String, contentUri: String) {
        dao.toggleStarred(stableKey, contentUri)
    }

    suspend fun setTags(stableKey: String, contentUri: String, tagIds: Set<Long>) {
        dao.replaceTags(stableKey, contentUri, tagIds)
    }
}
