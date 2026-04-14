package com.example.myapplication.utils

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.media.ExifInterface
import android.media.MediaMetadataRetriever
import android.net.Uri
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import java.io.File
import java.io.FileOutputStream
import java.io.IOException

/**
 * 缩略图生成工具类
 * 用于为图片和视频文件生成缩略图
 */
class ThumbnailGenerator(private val context: Context) {

    companion object {
        private const val THUMBNAIL_SIZE = 720 // 缩略图最大尺寸
        private const val THUMBNAIL_QUALITY = 85 // JPEG压缩质量
        private const val THUMBNAIL_DIR = "thumbnails" // 缩略图目录
    }

    /**
     * 为媒体文件生成缩略图
     * @param filePath 媒体文件路径
     * @param isVideo 是否为视频文件
     * @return 缩略图文件路径，失败返回null
     */
    suspend fun generateThumbnail(filePath: String, isVideo: Boolean): String? {
        return try {
            val sourceFile = File(filePath)
            if (!sourceFile.exists()) {
                return null
            }

            // 创建缩略图目录
            val thumbnailDir = File(context.filesDir, THUMBNAIL_DIR)
            if (!thumbnailDir.exists()) {
                thumbnailDir.mkdirs()
            }

            // 生成缩略图文件名
            val thumbnailFileName = "${sourceFile.nameWithoutExtension}_thumb.jpg"
            val thumbnailFile = File(thumbnailDir, thumbnailFileName)

            // 生成缩略图
            val bitmap = if (isVideo) {
                generateVideoThumbnail(filePath)
            } else {
                generateImageThumbnail(filePath)
            }

            if (bitmap != null) {
                saveBitmapToFile(bitmap, thumbnailFile)
                bitmap.recycle()
                thumbnailFile.absolutePath
            } else {
                null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 为视频生成缩略图
     */
    private fun generateVideoThumbnail(videoPath: String): Bitmap? {
        var retriever: MediaMetadataRetriever? = null
        return try {
            retriever = MediaMetadataRetriever()
            retriever.setDataSource(videoPath)

            // 获取视频第1秒的帧作为缩略图
            val bitmap = retriever.getFrameAtTime(1000000) // 微秒

            if (bitmap != null) {
                // 缩放bitmap
                scaleBitmap(bitmap)
            } else {
                null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        } finally {
            try {
                retriever?.release()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    /**
     * 为图片生成缩略图
     */
    private fun generateImageThumbnail(imagePath: String): Bitmap? {
        return try {
            // 先获取图片尺寸
            val options = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            BitmapFactory.decodeFile(imagePath, options)

            // 计算合适的采样率
            options.inSampleSize = calculateInSampleSize(options, THUMBNAIL_SIZE, THUMBNAIL_SIZE)
            options.inJustDecodeBounds = false

            // 解码图片
            var bitmap = BitmapFactory.decodeFile(imagePath, options)

            if (bitmap != null) {
                // 处理EXIF旋转信息
                bitmap = rotateImageIfRequired(bitmap, imagePath)

                // 进一步缩放到指定尺寸
                scaleBitmap(bitmap)
            } else {
                null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 根据EXIF信息旋转图片
     */
    private fun rotateImageIfRequired(bitmap: Bitmap, imagePath: String): Bitmap {
        return try {
            val exif = ExifInterface(imagePath)
            val orientation = exif.getAttributeInt(
                ExifInterface.TAG_ORIENTATION,
                ExifInterface.ORIENTATION_NORMAL
            )

            when (orientation) {
                ExifInterface.ORIENTATION_ROTATE_90 -> rotateBitmap(bitmap, 90f)
                ExifInterface.ORIENTATION_ROTATE_180 -> rotateBitmap(bitmap, 180f)
                ExifInterface.ORIENTATION_ROTATE_270 -> rotateBitmap(bitmap, 270f)
                else -> bitmap
            }
        } catch (e: Exception) {
            e.printStackTrace()
            bitmap // 如果出错，返回原图
        }
    }

    /**
     * 旋转Bitmap
     */
    private fun rotateBitmap(bitmap: Bitmap, degrees: Float): Bitmap {
        return try {
            val matrix = Matrix().apply {
                postRotate(degrees)
            }
            val rotatedBitmap = Bitmap.createBitmap(
                bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true
            )
            if (rotatedBitmap != bitmap) {
                bitmap.recycle() // 释放原bitmap内存
            }
            rotatedBitmap
        } catch (e: Exception) {
            e.printStackTrace()
            bitmap // 如果旋转失败，返回原图
        }
    }

    /**
     * 缩放bitmap到指定尺寸
     */
    private fun scaleBitmap(source: Bitmap): Bitmap {
        val width = source.width
        val height = source.height

        // 如果已经足够小，直接返回
        if (width <= THUMBNAIL_SIZE && height <= THUMBNAIL_SIZE) {
            return source
        }

        // 计算缩放比例，保持宽高比
        val scale = minOf(
            THUMBNAIL_SIZE.toFloat() / width,
            THUMBNAIL_SIZE.toFloat() / height
        )

        val newWidth = (width * scale).toInt()
        val newHeight = (height * scale).toInt()

        return try {
            val scaledBitmap = Bitmap.createScaledBitmap(source, newWidth, newHeight, true)
            if (scaledBitmap != source) {
                source.recycle()
            }
            scaledBitmap
        } catch (e: OutOfMemoryError) {
            e.printStackTrace()
            source
        }
    }

    /**
     * 计算图片采样率
     */
    private fun calculateInSampleSize(
        options: BitmapFactory.Options,
        reqWidth: Int,
        reqHeight: Int
    ): Int {
        val height = options.outHeight
        val width = options.outWidth
        var inSampleSize = 1

        if (height > reqHeight || width > reqWidth) {
            val halfHeight = height / 2
            val halfWidth = width / 2

            while (halfHeight / inSampleSize >= reqHeight && halfWidth / inSampleSize >= reqWidth) {
                inSampleSize *= 2
            }
        }

        return inSampleSize
    }

    /**
     * 保存bitmap到文件
     */
    private fun saveBitmapToFile(bitmap: Bitmap, file: File): Boolean {
        return try {
            FileOutputStream(file).use { out ->
                bitmap.compress(Bitmap.CompressFormat.JPEG, THUMBNAIL_QUALITY, out)
            }
            true
        } catch (e: IOException) {
            e.printStackTrace()
            false
        }
    }

    /**
     * 从URI生成缩略图（用于文件选择器选中的文件）
     */
    suspend fun generateThumbnailFromUri(uri: Uri, isVideo: Boolean): String? {
        return try {
            // 创建缩略图目录
            val thumbnailDir = File(context.filesDir, THUMBNAIL_DIR)
            if (!thumbnailDir.exists()) {
                thumbnailDir.mkdirs()
            }

            // 生成临时缩略图文件名
            val thumbnailFileName = "temp_${System.currentTimeMillis()}_thumb.jpg"
            val thumbnailFile = File(thumbnailDir, thumbnailFileName)

            // 生成缩略图
            val bitmap = if (isVideo) {
                generateVideoThumbnailFromUri(uri)
            } else {
                generateImageThumbnailFromUri(uri)
            }

            if (bitmap != null) {
                saveBitmapToFile(bitmap, thumbnailFile)
                bitmap.recycle()
                thumbnailFile.absolutePath
            } else {
                null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 从URI为视频生成缩略图
     */
    private fun generateVideoThumbnailFromUri(uri: Uri): Bitmap? {
        var retriever: MediaMetadataRetriever? = null
        return try {
            retriever = MediaMetadataRetriever()
            retriever.setDataSource(context, uri)

            val bitmap = retriever.getFrameAtTime(1000000) // 1秒处的帧

            if (bitmap != null) {
                scaleBitmap(bitmap)
            } else {
                null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        } finally {
            try {
                retriever?.release()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    /**
     * 从URI为图片生成缩略图
     */
    private fun generateImageThumbnailFromUri(uri: Uri): Bitmap? {
        return try {
            context.contentResolver.openInputStream(uri)?.use { inputStream ->
                // 先获取图片尺寸
                val options = BitmapFactory.Options().apply {
                    inJustDecodeBounds = true
                }
                BitmapFactory.decodeStream(inputStream, null, options)

                // 重新打开流进行解码
                context.contentResolver.openInputStream(uri)?.use { decodeStream ->
                    // 计算采样率
                    options.inSampleSize =
                        calculateInSampleSize(options, THUMBNAIL_SIZE, THUMBNAIL_SIZE)
                    options.inJustDecodeBounds = false

                    // 解码图片
                    val bitmap = BitmapFactory.decodeStream(decodeStream, null, options)

                    if (bitmap != null) {
                        scaleBitmap(bitmap)
                    } else {
                        null
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }

    /**
     * 删除缩略图文件
     */
    fun deleteThumbnail(thumbnailPath: String): Boolean {
        return try {
            val file = File(thumbnailPath)
            if (file.exists()) {
                file.delete()
            } else {
                false
            }
        } catch (e: Exception) {
            e.printStackTrace()
            false
        }
    }

    /**
     * 加载缩略图为ImageBitmap（用于Compose显示）
     */
    fun loadThumbnailBitmap(thumbnailPath: String?): ImageBitmap? {
        if (thumbnailPath == null) return null

        return try {
            val file = File(thumbnailPath)
            if (file.exists()) {
                val bitmap = BitmapFactory.decodeFile(thumbnailPath)
                bitmap?.asImageBitmap()
            } else {
                null
            }
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}