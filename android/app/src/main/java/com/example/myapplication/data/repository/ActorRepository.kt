package com.example.myapplication.data.repository

import android.content.Context
import android.util.Log
import com.example.myapplication.data.database.dao.ActorDao
import com.example.myapplication.data.database.entities.Actor
import com.example.myapplication.data.database.entities.SyncOutboxItem
import com.example.myapplication.data.model.SyncResult
import com.example.myapplication.data.service.SyncConfig
import com.example.myapplication.data.service.SyncNetwork
import com.example.myapplication.data.service.buildFullUrl
import com.example.myapplication.utils.FileUtils
import com.google.gson.Gson
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.withContext
import java.io.File

/**
 * 演员数据仓库
 */
class ActorRepository(
    private val actorDao: ActorDao,
    private val outboxRepository: SyncOutboxRepository? = null
) {

    private val syncService by lazy { SyncNetwork.syncService }
    private val gson = Gson()

    // 查询操作
    fun getAllActors(): Flow<List<Actor>> = actorDao.getAllActors()

    suspend fun getActorById(id: Long): Actor? = actorDao.getActorById(id)


    fun searchActorsByName(query: String): Flow<List<Actor>> =
        actorDao.searchActorsByName(query)

    suspend fun getActorCount(): Int = actorDao.getActorCount()


    // 写入操作
    suspend fun insertActor(actor: Actor): Long {
        val insertedId = actorDao.insertActor(actor)

        // 本地新建也入队：使用生成后的 id 作为 entityId
        if (insertedId > 0) {
            val payload = actor.copy(id = insertedId)
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_ACTOR,
                entityId = insertedId,
                payloadJson = gson.toJson(payload)
            )
        }

        return insertedId
    }

    suspend fun insertActors(actors: List<Actor>): List<Long> {
        val ids = actorDao.insertActors(actors)

        // 入队：按 Room 返回的 id 顺序与输入顺序对应
        ids.forEachIndexed { index, id ->
            if (id > 0) {
                val payload = actors.getOrNull(index)?.copy(id = id) ?: return@forEachIndexed
                outboxRepository?.enqueueUpsert(
                    entityType = SyncOutboxItem.ENTITY_ACTOR,
                    entityId = id,
                    payloadJson = gson.toJson(payload)
                )
            }
        }

        return ids
    }

    suspend fun updateActor(actor: Actor) {
        // 更新时间戳
        val updatedActor = actor.copy(updatedAt = System.currentTimeMillis())
        actorDao.updateActor(updatedActor)

        // 仅对已有远端 id 的数据入队（避免本地新建 id 无法与服务端对齐）
        if (updatedActor.id > 0) {
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_ACTOR,
                entityId = updatedActor.id,
                payloadJson = gson.toJson(updatedActor)
            )
        }
    }

    suspend fun deleteActor(actor: Actor) {
        // 删除演员时，消息的actorId会保留（不级联删除）
        actorDao.deleteActor(actor)

        if (actor.id > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_ACTOR,
                entityId = actor.id
            )
        }
    }

    suspend fun deleteActorById(id: Long) {
        actorDao.deleteActorById(id)

        if (id > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_ACTOR,
                entityId = id
            )
        }
    }

    suspend fun deleteAllActors() {
        val allActors = actorDao.getAllActorsSync()
        actorDao.deleteAllActors()

        for (actor in allActors) {
            if (actor.id > 0) {
                outboxRepository?.enqueueDelete(
                    entityType = SyncOutboxItem.ENTITY_ACTOR,
                    entityId = actor.id
                )
            }
        }
    }


    // ==================== 远程同步相关方法（与 Media/Group 对齐） ====================

    /**
     * 从远程服务器同步演员数据（upsert，不删除本地多余数据）
     */
    suspend fun syncFromRemote(context: Context): SyncResult = withContext(Dispatchers.IO) {
        return@withContext try {
            Log.d(TAG, "开始从远程服务器同步演员数据...")

            val avatarsDir = File(context.filesDir, "avatars")
            if (!avatarsDir.exists()) avatarsDir.mkdirs()

            val remoteActors = syncService.getActors()
            Log.d(TAG, "获取到 ${remoteActors.size} 条远程演员数据")

            val existingIds = actorDao.getAllActorIdsSync().toSet()
            var insertedCount = 0
            var updatedCount = 0

            for (remote in remoteActors) {
                val localAvatarPath = downloadAvatar(
                    remoteAvatarPath = remote.avatar,
                    actorId = remote.id,
                    avatarsDir = avatarsDir
                )
                val localActor = remote.toLocalActor(avatarLocalPath = localAvatarPath).copy(
                    updatedAt = System.currentTimeMillis()
                )

                actorDao.insertActor(localActor)
                if (remote.id in existingIds) updatedCount++ else insertedCount++
            }

            Log.d(TAG, "同步完成：新增 $insertedCount 条，更新 $updatedCount 条")
            SyncResult.Success(insertedCount, updatedCount)
        } catch (e: Exception) {
            Log.e(TAG, "同步失败: ${e.message}", e)
            SyncResult.Error(e.message ?: "未知错误")
        }
    }

    /**
     * 从远程服务器全量同步（删除本地不存在于远程的演员）
     */
    suspend fun fullSyncFromRemote(context: Context): SyncResult = withContext(Dispatchers.IO) {
        return@withContext try {
            Log.d(TAG, "开始全量同步远程演员数据...")

            val avatarsDir = File(context.filesDir, "avatars")
            if (!avatarsDir.exists()) avatarsDir.mkdirs()

            val remoteActors = syncService.getActors()
            val remoteIds = remoteActors.map { it.id }.toSet()
            val existingIds = actorDao.getAllActorIdsSync().toSet()

            var insertedCount = 0
            var updatedCount = 0
            var deletedCount = 0

            if (remoteIds.isEmpty()) {
                // 远端为空：删除本地所有演员；仅清理 app 内下载的头像文件
                cleanupDownloadedAvatars(avatarsDir)
                actorDao.deleteAllActors()
                deletedCount = existingIds.size
                Log.d(TAG, "远端为空，已删除本地全部演员：$deletedCount 条")
            } else {
                val idsToDelete = existingIds - remoteIds
                for (id in idsToDelete) {
                    val actor = actorDao.getActorById(id)
                    actor?.avatarPath?.let { avatarPath ->
                        safeDeleteIfUnderDir(avatarPath = avatarPath, dir = avatarsDir)
                    }
                    actorDao.deleteActorById(id)
                }
                deletedCount = idsToDelete.size
                Log.d(TAG, "删除了 $deletedCount 条本地多余的演员")
            }

            for (remote in remoteActors) {
                val localAvatarPath = downloadAvatar(
                    remoteAvatarPath = remote.avatar,
                    actorId = remote.id,
                    avatarsDir = avatarsDir
                )
                val localActor = remote.toLocalActor(avatarLocalPath = localAvatarPath).copy(
                    updatedAt = System.currentTimeMillis()
                )

                actorDao.insertActor(localActor)
                if (remote.id in existingIds) updatedCount++ else insertedCount++
            }

            Log.d(
                TAG,
                "全量同步完成：新增 $insertedCount 条，更新 $updatedCount 条，删除 $deletedCount 条"
            )
            SyncResult.Success(insertedCount, updatedCount, deletedCount)
        } catch (e: Exception) {
            Log.e(TAG, "全量同步失败: ${e.message}", e)
            SyncResult.Error(e.message ?: "未知错误")
        }
    }

    private suspend fun downloadAvatar(
        remoteAvatarPath: String?,
        actorId: Long,
        avatarsDir: File
    ): String? {
        if (remoteAvatarPath.isNullOrBlank()) return null

        return try {
            val extension = remoteAvatarPath.substringAfterLast(".", "jpg")
            val fileName = "actor_${actorId}_avatar.$extension"
            val localFile = File(avatarsDir, fileName)

            if (!localFile.exists()) {
                val downloadUrl = buildFullUrl(SyncConfig.BASE_URL, remoteAvatarPath)
                val success = FileUtils.downloadFile(downloadUrl, localFile)
                if (success) localFile.absolutePath else null
            } else {
                localFile.absolutePath
            }
        } catch (e: Exception) {
            Log.w(TAG, "下载头像异常: ${e.message}", e)
            null
        }
    }

    private fun safeDeleteIfUnderDir(avatarPath: String, dir: File) {
        try {
            val file = File(avatarPath)
            if (!file.exists()) return

            val dirPath = dir.canonicalFile.absolutePath
            val filePath = file.canonicalFile.absolutePath
            if (filePath.startsWith(dirPath)) {
                file.delete()
            }
        } catch (_: Exception) {
        }
    }

    private fun cleanupDownloadedAvatars(avatarsDir: File) {
        try {
            avatarsDir.listFiles()?.forEach { file ->
                try {
                    if (file.isFile) file.delete()
                } catch (_: Exception) {
                }
            }
        } catch (_: Exception) {
        }
    }

    companion object {
        private const val TAG = "ActorRepository"
    }
}