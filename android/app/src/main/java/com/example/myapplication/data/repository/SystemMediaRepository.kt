package com.example.myapplication.data.repository

import android.content.ContentResolver
import android.content.Context
import android.database.Cursor
import android.net.Uri
import android.provider.MediaStore
import com.example.myapplication.data.model.SystemMedia
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn

/**
 * 系统媒体仓储类
 * 负责从 MediaStore 查询设备中的所有图片和视频文件
 */
class SystemMediaRepository(private val context: Context) {

    private val contentResolver: ContentResolver = context.contentResolver

    /**
     * 获取所有系统媒体（图片+视频）
     */
    fun getAllSystemMedia(): Flow<List<SystemMedia>> =
        getAccessibleSystemMedia(canReadImages = true, canReadVideos = true)

    /**
     * 仅查询已经获得读取权限的媒体 collection。
     */
    fun getAccessibleSystemMedia(
        canReadImages: Boolean,
        canReadVideos: Boolean
    ): Flow<List<SystemMedia>> = flow {
        val mediaList = buildList {
            if (canReadImages) addAll(queryImages())
            if (canReadVideos) addAll(queryVideos())
        }
        emit(sortMedia(mediaList))
    }.flowOn(Dispatchers.IO)

    /**
     * 仅获取图片
     */
    fun getImages(): Flow<List<SystemMedia>> = flow {
        emit(sortMedia(queryImages()))
    }.flowOn(Dispatchers.IO)

    /**
     * 仅获取视频
     */
    fun getVideos(): Flow<List<SystemMedia>> = flow {
        emit(sortMedia(queryVideos()))
    }.flowOn(Dispatchers.IO)

    /**
     * 按文件夹分组获取媒体
     */
    fun getMediaByBucket(): Flow<Map<String, List<SystemMedia>>> = flow {
        val allMedia = mutableListOf<SystemMedia>()
        allMedia.addAll(queryImages())
        allMedia.addAll(queryVideos())

        val groupedMedia = sortMedia(allMedia)
            .groupBy { it.bucketDisplayName ?: "其他" }

        emit(groupedMedia)
    }.flowOn(Dispatchers.IO)

    /**
     * 查询图片
     */
    private fun queryImages(id: Long? = null): List<SystemMedia> {
        val images = mutableListOf<SystemMedia>()

        val projection = arrayOf(
            MediaStore.Images.Media._ID,
            MediaStore.Images.Media.DISPLAY_NAME,
            MediaStore.Images.Media.RELATIVE_PATH,
            MediaStore.Images.Media.MIME_TYPE,
            MediaStore.Images.Media.SIZE,
            MediaStore.Images.Media.DATE_ADDED,
            MediaStore.Images.Media.DATE_MODIFIED,
            MediaStore.Images.Media.WIDTH,
            MediaStore.Images.Media.HEIGHT,
            MediaStore.Images.Media.BUCKET_DISPLAY_NAME,
            MediaStore.Images.Media.BUCKET_ID
        )

        val sortOrder = "${MediaStore.Images.Media.DATE_MODIFIED} DESC"

        val cursor: Cursor? = contentResolver.query(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
            projection,
            id?.let { "${MediaStore.Images.Media._ID} = ?" },
            id?.let { arrayOf(it.toString()) },
            sortOrder
        )

        cursor?.use {
            val idColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media._ID)
            val displayNameColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DISPLAY_NAME)
            val relativePathColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.RELATIVE_PATH)
            val mimeTypeColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.MIME_TYPE)
            val sizeColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.SIZE)
            val dateAddedColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DATE_ADDED)
            val dateModifiedColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.DATE_MODIFIED)
            val widthColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.WIDTH)
            val heightColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.HEIGHT)
            val bucketDisplayNameColumn =
                it.getColumnIndexOrThrow(MediaStore.Images.Media.BUCKET_DISPLAY_NAME)
            val bucketIdColumn = it.getColumnIndexOrThrow(MediaStore.Images.Media.BUCKET_ID)

            while (it.moveToNext()) {
                val id = it.getLong(idColumn)
                val uri = Uri.withAppendedPath(
                    MediaStore.Images.Media.EXTERNAL_CONTENT_URI,
                    id.toString()
                )

                val systemMedia = SystemMedia(
                    id = id,
                    uri = uri,
                    displayName = it.getString(displayNameColumn) ?: "",
                    relativePath = it.getString(relativePathColumn),
                    mimeType = it.getString(mimeTypeColumn) ?: "",
                    size = it.getLong(sizeColumn),
                    dateAdded = it.getLong(dateAddedColumn),
                    dateModified = it.getLong(dateModifiedColumn),
                    width = it.getInt(widthColumn),
                    height = it.getInt(heightColumn),
                    bucketDisplayName = it.getString(bucketDisplayNameColumn),
                    bucketId = it.getString(bucketIdColumn)
                )

                images.add(systemMedia)
            }
        }

        return images
    }

    /**
     * 查询视频
     */
    private fun queryVideos(id: Long? = null): List<SystemMedia> {
        val videos = mutableListOf<SystemMedia>()

        val projection = arrayOf(
            MediaStore.Video.Media._ID,
            MediaStore.Video.Media.DISPLAY_NAME,
            MediaStore.Video.Media.RELATIVE_PATH,
            MediaStore.Video.Media.MIME_TYPE,
            MediaStore.Video.Media.SIZE,
            MediaStore.Video.Media.DATE_ADDED,
            MediaStore.Video.Media.DATE_MODIFIED,
            MediaStore.Video.Media.WIDTH,
            MediaStore.Video.Media.HEIGHT,
            MediaStore.Video.Media.DURATION,
            MediaStore.Video.Media.BUCKET_DISPLAY_NAME,
            MediaStore.Video.Media.BUCKET_ID
        )

        val sortOrder = "${MediaStore.Video.Media.DATE_MODIFIED} DESC"

        val cursor: Cursor? = contentResolver.query(
            MediaStore.Video.Media.EXTERNAL_CONTENT_URI,
            projection,
            id?.let { "${MediaStore.Video.Media._ID} = ?" },
            id?.let { arrayOf(it.toString()) },
            sortOrder
        )

        cursor?.use {
            val idColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media._ID)
            val displayNameColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.DISPLAY_NAME)
            val relativePathColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.RELATIVE_PATH)
            val mimeTypeColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.MIME_TYPE)
            val sizeColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.SIZE)
            val dateAddedColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.DATE_ADDED)
            val dateModifiedColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.DATE_MODIFIED)
            val widthColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.WIDTH)
            val heightColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.HEIGHT)
            val durationColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.DURATION)
            val bucketDisplayNameColumn =
                it.getColumnIndexOrThrow(MediaStore.Video.Media.BUCKET_DISPLAY_NAME)
            val bucketIdColumn = it.getColumnIndexOrThrow(MediaStore.Video.Media.BUCKET_ID)

            while (it.moveToNext()) {
                val id = it.getLong(idColumn)
                val uri =
                    Uri.withAppendedPath(MediaStore.Video.Media.EXTERNAL_CONTENT_URI, id.toString())

                val systemMedia = SystemMedia(
                    id = id,
                    uri = uri,
                    displayName = it.getString(displayNameColumn) ?: "",
                    relativePath = it.getString(relativePathColumn),
                    mimeType = it.getString(mimeTypeColumn) ?: "",
                    size = it.getLong(sizeColumn),
                    dateAdded = it.getLong(dateAddedColumn),
                    dateModified = it.getLong(dateModifiedColumn),
                    width = it.getInt(widthColumn),
                    height = it.getInt(heightColumn),
                    duration = it.getLong(durationColumn),
                    bucketDisplayName = it.getString(bucketDisplayNameColumn),
                    bucketId = it.getString(bucketIdColumn)
                )

                videos.add(systemMedia)
            }
        }

        return videos
    }

    /**
     * 根据 collection 类型和 ID 获取单个媒体文件。
     */
    suspend fun getMediaById(id: Long, isVideo: Boolean = false): SystemMedia? =
        if (isVideo) queryVideos(id).firstOrNull() else queryImages(id).firstOrNull()

    suspend fun getMediaByUri(uri: Uri): SystemMedia? {
        val id = uri.lastPathSegment?.toLongOrNull() ?: return null
        return when {
            uri.toString().startsWith(MediaStore.Video.Media.EXTERNAL_CONTENT_URI.toString()) ->
                getMediaById(id, isVideo = true)

            uri.toString().startsWith(MediaStore.Images.Media.EXTERNAL_CONTENT_URI.toString()) ->
                getMediaById(id, isVideo = false)

            else -> null
        }
    }

    private fun sortMedia(media: List<SystemMedia>): List<SystemMedia> =
        media.sortedWith(
            compareByDescending<SystemMedia> { it.dateModified }
                .thenByDescending { it.dateAdded }
                .thenBy { it.stableKey }
        )
}