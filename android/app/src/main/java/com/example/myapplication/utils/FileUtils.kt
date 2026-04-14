package com.example.myapplication.utils

import android.content.Context
import android.net.Uri
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.InputStream
import java.security.MessageDigest

/**
 * 文件哈希工具类
 * 用于计算文件的哈希值，防止重复上传
 */
object FileHashUtil {

    /**
     * 计算文件的SHA-256哈希值
     * @param context Android 上下文
     * @param uri 文件URI
     * @return 文件的哈希值字符串，如果计算失败则返回null
     */
    suspend fun calculateFileHash(context: Context, uri: Uri): String? {
        return withContext(Dispatchers.IO) {
            try {
                val inputStream: InputStream? = context.contentResolver.openInputStream(uri)
                inputStream?.use { stream ->
                    val digest = MessageDigest.getInstance("SHA-256")
                    val buffer = ByteArray(8192)
                    var bytesRead: Int

                    while (stream.read(buffer).also { bytesRead = it } != -1) {
                        digest.update(buffer, 0, bytesRead)
                    }

                    // 将字节数组转换为十六进制字符串
                    digest.digest().joinToString("") { "%02x".format(it) }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }

    /**
     * 计算字节数组的哈希值
     * @param data 字节数组
     * @return 哈希值字符串
     */
    fun calculateHash(data: ByteArray): String {
        val digest = MessageDigest.getInstance("SHA-256")
        return digest.digest(data).joinToString("") { "%02x".format(it) }
    }

    /**
     * 验证文件是否与给定哈希值匹配
     * @param context Android 上下文
     * @param uri 文件URI
     * @param expectedHash 预期的哈希值
     * @return 是否匹配
     */
    suspend fun verifyFileHash(context: Context, uri: Uri, expectedHash: String): Boolean {
        val actualHash = calculateFileHash(context, uri)
        return actualHash?.equals(expectedHash, ignoreCase = true) ?: false
    }
}

/**
 * 文件工具类
 * 包含文件相关的通用工具函数
 */
object FileUtils {

    /**
     * 格式化文件大小显示
     * @param sizeInBytes 文件大小（字节）
     * @return 格式化后的文件大小字符串，如 "1.5 MB", "512 KB" 等
     */
    fun formatFileSize(sizeInBytes: Long): String {
        return when {
            sizeInBytes < 1024 -> "${sizeInBytes} B"
            sizeInBytes < 1024 * 1024 -> String.format("%.1f KB", sizeInBytes / 1024.0)
            sizeInBytes < 1024 * 1024 * 1024 -> String.format(
                "%.1f MB",
                sizeInBytes / (1024.0 * 1024)
            )

            else -> String.format("%.1f GB", sizeInBytes / (1024.0 * 1024 * 1024))
        }
    }

    /**
     * 下载文件到本地
     */
    suspend fun downloadFile(url: String, destFile: java.io.File): Boolean {
        return withContext(Dispatchers.IO) {
            try {
                if (destFile.exists()) {
                    destFile.delete()
                }
                destFile.parentFile?.mkdirs()

                java.net.URL(url).openStream().use { input ->
                    java.io.FileOutputStream(destFile).use { output ->
                        input.copyTo(output)
                    }
                }
                true
            } catch (e: Exception) {
                e.printStackTrace()
                false
            }
        }
    }
}