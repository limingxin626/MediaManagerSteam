package com.example.myapplication.data.database.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.myapplication.data.database.entities.SyncOutboxItem

@Dao
interface SyncOutboxDao {

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(item: SyncOutboxItem): Long

    @Update
    suspend fun update(item: SyncOutboxItem)

    @Query(
        "SELECT * FROM sync_outbox WHERE status = :status ORDER BY createdAt ASC LIMIT :limit"
    )
    suspend fun getByStatus(status: String = SyncOutboxItem.STATUS_PENDING, limit: Int = 200): List<SyncOutboxItem>

    @Query(
        "DELETE FROM sync_outbox WHERE status = :status"
    )
    suspend fun deleteByStatus(status: String)

    @Query(
        "DELETE FROM sync_outbox WHERE status = :status AND entityType = :entityType AND operation = :operation AND entityId = :entityId"
    )
    suspend fun deletePendingSameKey(
        status: String = SyncOutboxItem.STATUS_PENDING,
        entityType: String,
        operation: String,
        entityId: Long
    )

    @Query("UPDATE sync_outbox SET status = :status, updatedAt = :updatedAt WHERE id = :id")
    suspend fun updateStatus(id: Long, status: String, updatedAt: Long = System.currentTimeMillis())

    @Query(
        "UPDATE sync_outbox SET attemptCount = attemptCount + 1, lastError = :lastError, updatedAt = :updatedAt WHERE id = :id"
    )
    suspend fun markAttempt(id: Long, lastError: String?, updatedAt: Long = System.currentTimeMillis())
}
