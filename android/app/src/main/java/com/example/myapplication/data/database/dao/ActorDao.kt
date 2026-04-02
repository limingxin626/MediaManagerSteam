package com.example.myapplication.data.database.dao

import androidx.room.*
import com.example.myapplication.data.database.entities.Actor
import kotlinx.coroutines.flow.Flow

/**
 * 演员数据访问对象
 */
@Dao
interface ActorDao {
    
    // 查询所有演员
    @Query("SELECT * FROM actors ORDER BY name ASC")
    fun getAllActors(): Flow<List<Actor>>
    
    // 根据ID查询演员
    @Query("SELECT * FROM actors WHERE id = :id")
    suspend fun getActorById(id: Long): Actor?
    

    
    // 搜索演员（按姓名）
    @Query("SELECT * FROM actors WHERE name LIKE '%' || :query || '%' ORDER BY name ASC")
    fun searchActorsByName(query: String): Flow<List<Actor>>
    
    // 获取演员统计信息
    @Query("SELECT COUNT(*) FROM actors")
    suspend fun getActorCount(): Int
    
    // 插入演员
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertActor(actor: Actor): Long
    
    // 插入多个演员
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertActors(actors: List<Actor>): List<Long>
    
    // 更新演员
    @Update
    suspend fun updateActor(actor: Actor)
    
    // 删除演员
    @Delete
    suspend fun deleteActor(actor: Actor)
    
    // 根据ID删除演员
    @Query("DELETE FROM actors WHERE id = :id")
    suspend fun deleteActorById(id: Long)
    
    // 删除所有演员
    @Query("DELETE FROM actors")
    suspend fun deleteAllActors()

    // ==================== 同步辅助（以 id 为唯一标识） ====================

    /**
     * 同步获取所有演员ID
     */
    @Query("SELECT id FROM actors")
    suspend fun getAllActorIdsSync(): List<Long>

    /**
     * 同步获取所有演员
     */
    @Query("SELECT * FROM actors")
    suspend fun getAllActorsSync(): List<Actor>
}