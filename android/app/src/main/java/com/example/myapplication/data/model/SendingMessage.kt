package com.example.myapplication.data.model

import okhttp3.MediaType
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.RequestBody
import okio.BufferedSink
import java.io.File
import java.io.InputStream

class ProgressRequestBody(
    private val openStream: () -> InputStream,
    private val length: Long,
    private val mimeType: String,
    private val onProgress: (Float) -> Unit
) : RequestBody() {

    constructor(
        file: File,
        mimeType: String,
        onProgress: (Float) -> Unit
    ) : this(file::inputStream, file.length(), mimeType, onProgress)

    override fun contentType(): MediaType? = mimeType.toMediaTypeOrNull()

    override fun contentLength(): Long = length

    override fun writeTo(sink: BufferedSink) {
        val total = length.toFloat()
        var uploaded = 0L
        val buffer = ByteArray(8192)

        openStream().use { input ->
            var read: Int
            while (input.read(buffer).also { read = it } != -1) {
                sink.write(buffer, 0, read)
                uploaded += read
                onProgress(if (total > 0) uploaded / total else 1f)
            }
        }
    }
}
