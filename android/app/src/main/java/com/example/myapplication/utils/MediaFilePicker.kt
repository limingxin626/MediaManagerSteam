package com.example.myapplication.utils

import android.content.Context
import android.net.Uri
import android.provider.MediaStore
import android.provider.OpenableColumns
import androidx.activity.result.ActivityResultLauncher
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalContext
import android.media.ExifInterface

import org.bouncycastle.crypto.digests.Blake2bDigest
import java.io.File
import java.io.FileOutputStream
import java.io.InputStream

/**
 * 媒体文件选择器数据类
 */
data class MediaFileInfo(
    val uri: Uri,
    val fileName: String,
    val mimeType: String?,
    val size: Long,
    val localPath: String? = null
)

/**
 * 媒体文件选择器工具类
 */
class MediaFilePicker(private val context: Context) {

    /**
     * 获取文件信息
     */
    fun getFileInfo(uri: Uri): MediaFileInfo? {
        return try {
            val cursor = context.contentResolver.query(
                uri, null, null, null, null
            )
            cursor?.use {
                if (it.moveToFirst()) {
                    val nameIndex = it.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    val sizeIndex = it.getColumnIndex(OpenableColumns.SIZE)
                    
                    val fileName = if (nameIndex != -1) it.getString(nameIndex) else "unknown"
                    val size = if (sizeIndex != -1) it.getLong(sizeIndex) else 0L
                    val mimeType = context.contentResolver.getType(uri)
                    
                    MediaFileInfo(
                        uri = uri,
                        fileName = fileName,
                        mimeType = mimeType,
                        size = size
                    )
                } else null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 复制文件到应用私有存储
     */
    fun copyFileToAppStorage(uri: Uri, fileName: String): String? {
        return try {
            val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
            inputStream?.use { input ->
                val filesDir = File(context.filesDir, "media")
                if (!filesDir.exists()) {
                    filesDir.mkdirs()
                }
                
                val outputFile = File(filesDir, fileName)
                val outputStream = FileOutputStream(outputFile)
                
                outputStream.use { output ->
                    input.copyTo(output)
                }
                
                outputFile.absolutePath
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 根据MIME类型判断媒体类型
     */
    fun getMediaType(mimeType: String?): String {
        return when {
            mimeType?.startsWith("video/") == true -> "VIDEO"
            mimeType?.startsWith("image/") == true -> "IMAGE"
            else -> "IMAGE" // 默认为图片
        }
    }

    /**
     * 获取视频时长（秒）
     */
    fun getVideoDuration(uri: Uri): Long? {
        return try {
            val cursor = context.contentResolver.query(
                uri,
                arrayOf(MediaStore.Video.Media.DURATION),
                null,
                null,
                null
            )
            cursor?.use {
                if (it.moveToFirst()) {
                    val durationIndex = it.getColumnIndex(MediaStore.Video.Media.DURATION)
                    if (durationIndex != -1) {
                        it.getLong(durationIndex) / 1000 // 转换为秒
                    } else null
                } else null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 获取图片/视频分辨率（考虑EXIF旋转）
     */
    fun getMediaResolution(uri: Uri): String? {
        return try {
            val cursor = context.contentResolver.query(
                uri,
                arrayOf(
                    MediaStore.Images.Media.WIDTH,
                    MediaStore.Images.Media.HEIGHT
                ),
                null,
                null,
                null
            )
            cursor?.use {
                if (it.moveToFirst()) {
                    val widthIndex = it.getColumnIndex(MediaStore.Images.Media.WIDTH)
                    val heightIndex = it.getColumnIndex(MediaStore.Images.Media.HEIGHT)
                    
                    if (widthIndex != -1 && heightIndex != -1) {
                        var width = it.getInt(widthIndex)
                        var height = it.getInt(heightIndex)
                        
                        if (width > 0 && height > 0) {
                            // 检查EXIF旋转信息，如果是90度或270度旋转，需要交换宽高
                            val mimeType = context.contentResolver.getType(uri)
                            if (mimeType?.startsWith("image/") == true) {
                                val rotation = getExifRotation(uri)
                                if (rotation == 90 || rotation == 270) {
                                    // 交换宽高
                                    val temp = width
                                    width = height
                                    height = temp
                                }
                            }
                            "${width}x${height}"
                        } else null
                    } else null
                } else null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
    
    /**
     * 使用BLAKE2b计算文件内容哈希
     */
    fun computeBlake2bHash(uri: Uri): String? {
        return try {
            val digest = Blake2bDigest(256)
            val buffer = ByteArray(8192)
            context.contentResolver.openInputStream(uri)?.use { input ->
                var bytesRead: Int
                while (input.read(buffer).also { bytesRead = it } != -1) {
                    digest.update(buffer, 0, bytesRead)
                }
            }
            val result = ByteArray(digest.digestSize)
            digest.doFinal(result, 0)
            result.joinToString("") { "%02x".format(it) }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 获取图片EXIF旋转角度
     */
    private fun getExifRotation(uri: Uri): Int {
        return try {
            // 对于content:// URI，我们需要先复制文件或使用文件描述符
            // 这里简化处理，先尝试直接从MediaStore获取方向信息
            val cursor = context.contentResolver.query(
                uri,
                arrayOf(MediaStore.Images.Media.ORIENTATION),
                null,
                null,
                null
            )
            cursor?.use {
                if (it.moveToFirst()) {
                    val orientationIndex = it.getColumnIndex(MediaStore.Images.Media.ORIENTATION)
                    if (orientationIndex != -1) {
                        it.getInt(orientationIndex)
                    } else 0
                } else 0
            } ?: 0
        } catch (e: Exception) {
            e.printStackTrace()
            0
        }
    }
}

/**
 * 视频选择器 Hook（从相册选择视频）
 */
@Composable
fun rememberVideoFilePicker(
    onVideoSelected: (MediaFileInfo) -> Unit
): ActivityResultLauncher<PickVisualMediaRequest> {
    val context = LocalContext.current
    val filePicker = remember { MediaFilePicker(context) }
    
    return androidx.activity.compose.rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        uri?.let { 
            filePicker.getFileInfo(it)?.let { fileInfo ->
                onVideoSelected(fileInfo)
            }
        }
    }
}

/**
 * 图片选择器 Hook（从相册选择图片）
 */
@Composable
fun rememberImageFilePicker(
    onImageSelected: (MediaFileInfo) -> Unit
): ActivityResultLauncher<PickVisualMediaRequest> {
    val context = LocalContext.current
    val filePicker = remember { MediaFilePicker(context) }
    
    return androidx.activity.compose.rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        uri?.let { 
            filePicker.getFileInfo(it)?.let { fileInfo ->
                onImageSelected(fileInfo)
            }
        }
    }
}

/**
 * Compose 媒体选择器 Hook（使用系统相册）
 */
@Composable
fun rememberMediaFilePicker(
    onMediaSelected: (MediaFileInfo) -> Unit
): ActivityResultLauncher<PickVisualMediaRequest> {
    val context = LocalContext.current
    val filePicker = remember { MediaFilePicker(context) }

    return androidx.activity.compose.rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickVisualMedia()
    ) { uri ->
        uri?.let {
            filePicker.getFileInfo(it)?.let { fileInfo ->
                onMediaSelected(fileInfo)
            }
        }
    }
}

/**
 * 多媒体选择器 Hook（支持多选）
 */
@Composable
fun rememberMultipleMediaFilePicker(
    maxItems: Int = 10,
    onMediaSelected: (List<MediaFileInfo>) -> Unit
): ActivityResultLauncher<PickVisualMediaRequest> {
    val context = LocalContext.current
    val filePicker = remember { MediaFilePicker(context) }
    
    return androidx.activity.compose.rememberLauncherForActivityResult(
        contract = ActivityResultContracts.PickMultipleVisualMedia(maxItems)
    ) { uris ->
        if (uris.isNotEmpty()) {
            val mediaFiles = uris.mapNotNull { uri ->
                filePicker.getFileInfo(uri)
            }
            onMediaSelected(mediaFiles)
        }
    }
}