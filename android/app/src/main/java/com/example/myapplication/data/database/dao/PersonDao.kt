package com.example.myapplication.data.database.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import com.example.myapplication.data.database.entities.MediaPerson
import com.example.myapplication.data.database.entities.Person
import kotlinx.coroutines.flow.Flow

/**
 * 人物数据访问对象(含 media_person 关联读写)
 */
@Dao
interface PersonDao {

    // 查询所有人物
    @Query("SELECT * FROM people ORDER BY name ASC")
    fun getAllPeople(): Flow<List<Person>>

    // 根据ID查询人物
    @Query("SELECT * FROM people WHERE id = :id")
    suspend fun getPersonById(id: Long): Person?

    // 搜索人物(按名称)
    @Query("SELECT * FROM people WHERE name LIKE '%' || :query || '%' ORDER BY name ASC")
    fun searchPeopleByName(query: String): Flow<List<Person>>

    // 获取人物统计信息
    @Query("SELECT COUNT(*) FROM people")
    suspend fun getPersonCount(): Int

    // 插入人物(已存在则跳过)
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertPersonIgnore(person: Person): Long

    // 插入或更新人物
    suspend fun insertPerson(person: Person): Long {
        val insertedId = insertPersonIgnore(person)
        if (insertedId == -1L) {
            updatePerson(person)
            return person.id
        }
        return insertedId
    }

    // 更新人物
    @Update
    suspend fun updatePerson(person: Person)

    // 删除人物
    @Delete
    suspend fun deletePerson(person: Person)

    // 根据ID删除人物
    @Query("DELETE FROM people WHERE id = :id")
    suspend fun deletePersonById(id: Long)

    // 删除所有人物
    @Query("DELETE FROM people")
    suspend fun deleteAllPeople()

    // ==================== media_person 关联 ====================

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertMediaPeople(refs: List<MediaPerson>)

    /** 删除某 media 的所有人物关联 */
    @Query("DELETE FROM media_people WHERE mediaId = :mediaId")
    suspend fun deleteMediaPeopleByMediaId(mediaId: Long)

    /** 按 mediaId 全量替换该 media 的人物关联 */
    @androidx.room.Transaction
    suspend fun replaceMediaPeople(mediaId: Long, refs: List<MediaPerson>) {
        deleteMediaPeopleByMediaId(mediaId)
        if (refs.isNotEmpty()) insertMediaPeople(refs)
    }

    // ==================== 同步辅助 ====================

    @Query("SELECT id FROM people")
    suspend fun getAllPersonIdsSync(): List<Long>

    @Query("SELECT * FROM people")
    suspend fun getAllPeopleSync(): List<Person>
}
