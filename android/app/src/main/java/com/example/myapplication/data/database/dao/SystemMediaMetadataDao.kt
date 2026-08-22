package com.example.myapplication.data.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.example.myapplication.data.database.entities.SystemMediaMetadata
import com.example.myapplication.data.database.entities.SystemMediaTag
import kotlinx.coroutines.flow.Flow

@Dao
interface SystemMediaMetadataDao {
    @Query("SELECT * FROM system_media_metadata")
    fun observeAllMetadata(): Flow<List<SystemMediaMetadata>>

    @Query("SELECT * FROM system_media_tag")
    fun observeAllTagLinks(): Flow<List<SystemMediaTag>>

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMetadata(metadata: SystemMediaMetadata)

    @Transaction
    suspend fun toggleStarred(stableKey: String, contentUri: String) {
        insertMetadata(SystemMediaMetadata(stableKey, contentUri))
        toggleExistingStarred(stableKey, contentUri)
    }

    @Query(
        "UPDATE system_media_metadata SET contentUri = :contentUri, starred = NOT starred, " +
            "updatedAt = :updatedAt WHERE stableKey = :stableKey"
    )
    suspend fun toggleExistingStarred(
        stableKey: String,
        contentUri: String,
        updatedAt: Long = System.currentTimeMillis()
    )

    @Query("DELETE FROM system_media_tag WHERE systemMediaKey = :stableKey")
    suspend fun deleteTags(stableKey: String)

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertTagLinks(links: List<SystemMediaTag>)

    @Transaction
    suspend fun replaceTags(
        stableKey: String,
        contentUri: String,
        tagIds: Set<Long>
    ) {
        ensureMetadata(stableKey, contentUri)
        deleteTags(stableKey)
        insertTagLinks(tagIds.map { SystemMediaTag(stableKey, it) })
    }

    @Query(
        "INSERT OR IGNORE INTO system_media_metadata " +
            "(stableKey, contentUri, starred, updatedAt) VALUES (:stableKey, :contentUri, 0, :updatedAt)"
    )
    suspend fun ensureMetadata(
        stableKey: String,
        contentUri: String,
        updatedAt: Long = System.currentTimeMillis()
    )
}
