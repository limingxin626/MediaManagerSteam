package com.example.myapplication.data.repository

import android.content.Context
import android.util.Log
import com.example.myapplication.data.database.dao.CollectionDao
import com.example.myapplication.data.database.entities.Collection
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
 * 合集数据仓库(原 ActorRepository)
 */
class CollectionRepository(
    private val collectionDao: CollectionDao,
    private val outboxRepository: SyncOutboxRepository? = null
) {

    private val syncService by lazy { SyncNetwork.syncService }
    private val gson = Gson()

    // 查询操作
    fun getAllCollections(): Flow<List<Collection>> = collectionDao.getAllCollections()

    suspend fun getCollectionById(id: Long): Collection? = collectionDao.getCollectionById(id)


    fun searchCollectionsByName(query: String): Flow<List<Collection>> =
        collectionDao.searchCollectionsByName(query)

    suspend fun getCollectionCount(): Int = collectionDao.getCollectionCount()


    // 写入操作
    suspend fun insertCollection(collection: Collection): Long {
        val insertedId = collectionDao.insertCollection(collection)

        // 本地新建也入队：使用生成后的 id 作为 entityId
        if (insertedId > 0) {
            val payload = collection.copy(id = insertedId)
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_COLLECTION,
                entityId = insertedId,
                payloadJson = gson.toJson(payload)
            )
        }

        return insertedId
    }

    suspend fun insertCollections(collections: List<Collection>): List<Long> {
        val ids = collectionDao.insertCollections(collections)

        // 入队：按 Room 返回的 id 顺序与输入顺序对应
        ids.forEachIndexed { index, id ->
            if (id > 0) {
                val payload = collections.getOrNull(index)?.copy(id = id) ?: return@forEachIndexed
                outboxRepository?.enqueueUpsert(
                    entityType = SyncOutboxItem.ENTITY_COLLECTION,
                    entityId = id,
                    payloadJson = gson.toJson(payload)
                )
            }
        }

        return ids
    }

    suspend fun updateCollection(collection: Collection) {
        // 更新时间戳
        val updatedCollection = collection.copy(updatedAt = System.currentTimeMillis())
        collectionDao.updateCollection(updatedCollection)

        // 仅对已有远端 id 的数据入队（避免本地新建 id 无法与服务端对齐）
        if (updatedCollection.id > 0) {
            outboxRepository?.enqueueUpsert(
                entityType = SyncOutboxItem.ENTITY_COLLECTION,
                entityId = updatedCollection.id,
                payloadJson = gson.toJson(updatedCollection)
            )
        }
    }

    suspend fun deleteCollection(collection: Collection) {
        // 删除合集时，消息的 collectionId 会保留（不级联删除）
        collectionDao.deleteCollection(collection)

        if (collection.id > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_COLLECTION,
                entityId = collection.id
            )
        }
    }

    suspend fun deleteCollectionById(id: Long) {
        collectionDao.deleteCollectionById(id)

        if (id > 0) {
            outboxRepository?.enqueueDelete(
                entityType = SyncOutboxItem.ENTITY_COLLECTION,
                entityId = id
            )
        }
    }

    suspend fun deleteAllCollections() {
        val allCollections = collectionDao.getAllCollectionsSync()
        collectionDao.deleteAllCollections()

        for (collection in allCollections) {
            if (collection.id > 0) {
                outboxRepository?.enqueueDelete(
                    entityType = SyncOutboxItem.ENTITY_COLLECTION,
                    entityId = collection.id
                )
            }
        }
    }


    // ==================== 远程同步相关方法（与 Media/Group 对齐） ====================

    /**
     * 从远程服务器同步合集数据（upsert，不删除本地多余数据）
     */
    suspend fun syncFromRemote(context: Context): SyncResult = withContext(Dispatchers.IO) {
        return@withContext try {
            Log.d(TAG, "开始从远程服务器同步合集数据...")

            val coversDir = File(context.filesDir, "collection_covers")
            if (!coversDir.exists()) coversDir.mkdirs()

            val remoteCollections = syncService.getCollections()
            Log.d(TAG, "获取到 ${remoteCollections.size} 条远程合集数据")

            val existingIds = collectionDao.getAllCollectionIdsSync().toSet()
            var insertedCount = 0
            var updatedCount = 0

            for (remote in remoteCollections) {
                val localCoverPath = downloadCover(
                    remoteCoverPath = remote.cover,
                    collectionId = remote.id,
                    coversDir = coversDir
                )
                val localCollection = remote.toLocalCollection(coverLocalPath = localCoverPath).copy(
                    updatedAt = System.currentTimeMillis()
                )

                collectionDao.insertCollection(localCollection)
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
     * 从远程服务器全量同步（删除本地不存在于远程的合集）
     */
    suspend fun fullSyncFromRemote(context: Context): SyncResult = withContext(Dispatchers.IO) {
        return@withContext try {
            Log.d(TAG, "开始全量同步远程合集数据...")

            val coversDir = File(context.filesDir, "collection_covers")
            if (!coversDir.exists()) coversDir.mkdirs()

            val remoteCollections = syncService.getCollections()
            val remoteIds = remoteCollections.map { it.id }.toSet()
            val existingIds = collectionDao.getAllCollectionIdsSync().toSet()

            var insertedCount = 0
            var updatedCount = 0
            var deletedCount = 0

            if (remoteIds.isEmpty()) {
                // 远端为空：删除本地所有合集；仅清理 app 内下载的封面文件
                cleanupDownloadedCovers(coversDir)
                collectionDao.deleteAllCollections()
                deletedCount = existingIds.size
                Log.d(TAG, "远端为空，已删除本地全部合集：$deletedCount 条")
            } else {
                val idsToDelete = existingIds - remoteIds
                for (id in idsToDelete) {
                    val collection = collectionDao.getCollectionById(id)
                    collection?.coverPath?.let { coverPath ->
                        safeDeleteIfUnderDir(coverPath = coverPath, dir = coversDir)
                    }
                    collectionDao.deleteCollectionById(id)
                }
                deletedCount = idsToDelete.size
                Log.d(TAG, "删除了 $deletedCount 条本地多余的合集")
            }

            for (remote in remoteCollections) {
                val localCoverPath = downloadCover(
                    remoteCoverPath = remote.cover,
                    collectionId = remote.id,
                    coversDir = coversDir
                )
                val localCollection = remote.toLocalCollection(coverLocalPath = localCoverPath).copy(
                    updatedAt = System.currentTimeMillis()
                )

                collectionDao.insertCollection(localCollection)
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

    private suspend fun downloadCover(
        remoteCoverPath: String?,
        collectionId: Long,
        coversDir: File
    ): String? {
        if (remoteCoverPath.isNullOrBlank()) return null

        return try {
            val extension = remoteCoverPath.substringAfterLast(".", "webp")
            val fileName = "collection_${collectionId}_cover.$extension"
            val localFile = File(coversDir, fileName)

            if (!localFile.exists()) {
                val downloadUrl = buildFullUrl(SyncConfig.BASE_URL, remoteCoverPath)
                val success = FileUtils.downloadFile(downloadUrl, localFile)
                if (success) localFile.absolutePath else null
            } else {
                localFile.absolutePath
            }
        } catch (e: Exception) {
            Log.w(TAG, "下载封面异常: ${e.message}", e)
            null
        }
    }

    private fun safeDeleteIfUnderDir(coverPath: String, dir: File) {
        try {
            val file = File(coverPath)
            if (!file.exists()) return

            val dirPath = dir.canonicalFile.absolutePath
            val filePath = file.canonicalFile.absolutePath
            if (filePath.startsWith(dirPath)) {
                file.delete()
            }
        } catch (_: Exception) {
        }
    }

    private fun cleanupDownloadedCovers(coversDir: File) {
        try {
            coversDir.listFiles()?.forEach { file ->
                try {
                    if (file.isFile) file.delete()
                } catch (_: Exception) {
                }
            }
        } catch (_: Exception) {
        }
    }

    companion object {
        private const val TAG = "CollectionRepository"
    }
}
