package com.example.myapplication.data.repository

import com.example.myapplication.data.database.dao.PersonDao
import com.example.myapplication.data.database.entities.Person
import com.example.myapplication.data.database.entities.SyncOutboxItem
import com.google.gson.Gson
import kotlinx.coroutines.flow.Flow

/**
 * 人物数据仓库
 *
 * 注意:后端没有 person 列表全量端点,人物数据通过增量同步(/sync/changes 的 PERSON 变更 +
 * media 快照的 people[])落库,由 MessageRepository 处理。本仓库负责本地查询与本地变更入队推送。
 */
class PersonRepository(
    private val personDao: PersonDao,
    private val outboxRepository: SyncOutboxRepository? = null
) {

    private val gson = Gson()

    // 查询操作
    fun getAllPeople(): Flow<List<Person>> = personDao.getAllPeople()

    suspend fun getPersonById(id: Long): Person? = personDao.getPersonById(id)

    fun searchPeopleByName(query: String): Flow<List<Person>> =
        personDao.searchPeopleByName(query)

    suspend fun getPersonCount(): Int = personDao.getPersonCount()

    // 写入操作
    suspend fun insertPerson(person: Person): Long {
        val insertedId = personDao.insertPerson(person)
        if (insertedId > 0) {
            val payload = person.copy(id = insertedId)
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_PERSON,
                entityId = insertedId,
                payloadJson = gson.toJson(payload)
            )
        }
        return insertedId
    }

    suspend fun updatePerson(person: Person) {
        val updated = person.copy(updatedAt = System.currentTimeMillis())
        personDao.updatePerson(updated)
        if (updated.id > 0) {
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_PERSON,
                entityId = updated.id,
                payloadJson = gson.toJson(updated)
            )
        }
    }

    suspend fun deletePersonById(id: Long) {
        personDao.deletePersonById(id)
        if (id > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_PERSON,
                entityId = id
            )
        }
    }
}
