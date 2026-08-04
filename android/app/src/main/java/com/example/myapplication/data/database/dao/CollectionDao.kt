package com.example.myapplication.data.database.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.myapplication.data.database.entities.Collection
import kotlinx.coroutines.flow.Flow

/**
 * 合集数据访问对象(原 ActorDao)
 */
@Dao
interface CollectionDao {

    // 查询所有合集
    @Query("SELECT * FROM collections ORDER BY name ASC")
    fun getAllCollections(): Flow<List<Collection>>

    // 根据ID查询合集
    @Query("SELECT * FROM collections WHERE id = :id")
    suspend fun getCollectionById(id: Long): Collection?


    // 搜索合集(按名称)
    @Query("SELECT * FROM collections WHERE name LIKE '%' || :query || '%' ORDER BY name ASC")
    fun searchCollectionsByName(query: String): Flow<List<Collection>>

    // 获取合集统计信息
    @Query("SELECT COUNT(*) FROM collections")
    suspend fun getCollectionCount(): Int

    // 插入合集(已存在则跳过,不触发 DELETE 导致 Message.collectionId SET_NULL)
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertCollectionIgnore(collection: Collection): Long

    // 插入或更新合集
    suspend fun insertCollection(collection: Collection): Long {
        val insertedId = insertCollectionIgnore(collection)
        if (insertedId == -1L) {
            // 已存在,更新
            updateCollection(collection)
            return collection.id
        }
        return insertedId
    }

    // 插入多个合集(已存在则跳过,再逐个更新已存在的)
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertCollectionsIgnore(collections: List<Collection>): List<Long>

    suspend fun insertCollections(collections: List<Collection>): List<Long> {
        val results = insertCollectionsIgnore(collections)
        return results.mapIndexed { index, id ->
            if (id == -1L) {
                updateCollection(collections[index])
                collections[index].id
            } else {
                id
            }
        }
    }

    // 更新合集
    @Update
    suspend fun updateCollection(collection: Collection)

    // 删除合集
    @Delete
    suspend fun deleteCollection(collection: Collection)

    // 根据ID删除合集
    @Query("DELETE FROM collections WHERE id = :id")
    suspend fun deleteCollectionById(id: Long)

    // 删除所有合集
    @Query("DELETE FROM collections")
    suspend fun deleteAllCollections()

    // ==================== 同步辅助(以 id 为唯一标识) ====================

    /**
     * 同步获取所有合集ID
     */
    @Query("SELECT id FROM collections")
    suspend fun getAllCollectionIdsSync(): List<Long>

    /**
     * 同步获取所有合集
     */
    @Query("SELECT * FROM collections")
    suspend fun getAllCollectionsSync(): List<Collection>
}
