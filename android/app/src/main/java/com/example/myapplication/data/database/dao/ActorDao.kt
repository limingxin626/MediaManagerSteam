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
    
    // 插入演员（已存在则跳过，不触发 DELETE 导致 Message.actorId SET_NULL）
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertActorIgnore(actor: Actor): Long

    // 插入或更新演员
    suspend fun insertActor(actor: Actor): Long {
        val insertedId = insertActorIgnore(actor)
        if (insertedId == -1L) {
            // 已存在，更新
            updateActor(actor)
            return actor.id
        }
        return insertedId
    }

    // 插入多个演员（已存在则跳过，再逐个更新已存在的）
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertActorsIgnore(actors: List<Actor>): List<Long>

    suspend fun insertActors(actors: List<Actor>): List<Long> {
        val results = insertActorsIgnore(actors)
        return results.mapIndexed { index, id ->
            if (id == -1L) {
                updateActor(actors[index])
                actors[index].id
            } else {
                id
            }
        }
    }
    
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