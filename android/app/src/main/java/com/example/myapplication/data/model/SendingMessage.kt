package com.example.myapplication.data.model

import com.example.myapplication.utils.MediaFileInfo
import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody
import okio.BufferedSink
import java.io.File

enum class SendStatus { PREPARING, UPLOADING, CREATING, DONE, FAILED }

data class MediaUploadState(
    val mediaFileInfo: MediaFileInfo,
    val localMediaId: Long,
    val localFilePath: String?,          // 已复制到 app 私有存储的绝对路径
    val uploadProgress: Float = 0f,
    val serverPath: String? = null,
    val error: String? = null
)

data class SendingMessage(
    val tempId: String,
    val localMessageId: Long,
    val text: String?,
    val actorId: Long?,
    val mediaStates: List<MediaUploadState>,
    val status: SendStatus = SendStatus.PREPARING,
    val error: String? = null,
    val createdAt: Long = System.currentTimeMillis()
)

class ProgressRequestBody(
    private val file: File,
    private val mimeType: String,
    private val onProgress: (Float) -> Unit
) : RequestBody() {

    override fun contentType(): MediaType? = mimeType.toMediaTypeOrNull()

    override fun contentLength(): Long = file.length()

    override fun writeTo(sink: BufferedSink) {
        val total = file.length().toFloat()
        var uploaded = 0L
        val buffer = ByteArray(8192)

        file.inputStream().use { input ->
            var read: Int
            while (input.read(buffer).also { read = it } != -1) {
                sink.write(buffer, 0, read)
                uploaded += read
                onProgress(if (total > 0) uploaded / total else 1f)
            }
        }
    }
}
