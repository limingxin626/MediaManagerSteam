package com.example.myapplication.ui.components

import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.*
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.utils.MediaAdditionHelper
import com.example.myapplication.utils.rememberMediaAdditionManager
import com.example.myapplication.utils.rememberMediaFilePicker
import com.example.myapplication.utils.rememberMultipleMediaFilePicker

/**
 * 统一媒体选择器配置
 */
data class UnifiedMediaPickerConfig(
    val description: String = "添加媒体",
    val autoConnectToActor: Long? = null,
    val actorRole: String? = null,
    val allowMultiple: Boolean = true,  // 默认启用多选
    val maxItems: Int = 50            // 多选时的最大选择数量
)

/**
 * 统一媒体选择器回调
 */
interface UnifiedMediaPickerCallback {
    fun onSuccess(mediaId: Long, media: Media)
    fun onError(error: String)
    fun onProcessingStateChanged(isProcessing: Boolean)
    
    // 多选支持
    fun onMultipleSuccess(results: List<Pair<Long, Media>>) {
        // 默认实现：逐个调用单个成功回调
        results.forEach { (mediaId, media) ->
            onSuccess(mediaId, media)
        }
    }
}

/**
 * 统一媒体选择器
 * 支持同时选择视频和图片，自动识别文件类型并处理
 */
@Composable
fun rememberUnifiedMediaPicker(
    databaseManager: DatabaseManager,
    coroutineScope: CoroutineScope,
    config: UnifiedMediaPickerConfig = UnifiedMediaPickerConfig(),
    callback: UnifiedMediaPickerCallback
): () -> Unit {
    // 媒体添加管理器
    val mediaManager = rememberMediaAdditionManager(
        databaseManager = databaseManager,
        coroutineScope = coroutineScope,
        config = MediaAdditionHelper.MediaAdditionConfig(
            description = config.description,
            autoConnectToActor = config.autoConnectToActor,
            actorRole = config.actorRole ?: ""
        ),
        callback = object : MediaAdditionHelper.MediaAdditionCallback {
            override fun onSuccess(mediaId: Long, media: Media) {
                callback.onSuccess(mediaId, media)
            }

            override fun onError(error: String) {
                callback.onError(error)
            }

            override fun onProcessingStateChanged(isProcessing: Boolean) {
                callback.onProcessingStateChanged(isProcessing)
            }
        }
    )

    // 文件选择器
    val mediaPickerLauncher = rememberMediaFilePicker { fileInfo ->
        coroutineScope.launch {
            callback.onProcessingStateChanged(true)
            
            // 判断文件类型并调用相应的处理方法
            val mimeType = fileInfo.mimeType ?: ""
            val helperConfig = MediaAdditionHelper.MediaAdditionConfig(
                description = config.description,
                autoConnectToActor = config.autoConnectToActor,
                actorRole = config.actorRole ?: ""
            )
            val helperCallback = object : MediaAdditionHelper.MediaAdditionCallback {
                override fun onSuccess(mediaId: Long, media: Media) {
                    coroutineScope.launch {
                        callback.onProcessingStateChanged(false)
                        callback.onSuccess(mediaId, media)
                    }
                }
                override fun onError(error: String) {
                    coroutineScope.launch {
                        callback.onProcessingStateChanged(false)
                        callback.onError(error)
                    }
                }
                override fun onProcessingStateChanged(isProcessing: Boolean) {
                    coroutineScope.launch {
                        callback.onProcessingStateChanged(isProcessing)
                    }
                }
            }
            
            when {
                mimeType.startsWith("video/") -> {
                    mediaManager.helper.addVideoFromFile(fileInfo, helperConfig, helperCallback)
                }
                mimeType.startsWith("image/") -> {
                    mediaManager.helper.addImageFromFile(fileInfo, helperConfig, helperCallback)
                }
                else -> {
                    callback.onProcessingStateChanged(false)
                    callback.onError("不支持的文件类型")
                }
            }
        }
    }

    // 多选媒体选择器
    val multipleMediaPickerLauncher = if (config.allowMultiple) {
        rememberMultipleMediaFilePicker(
            maxItems = config.maxItems
        ) { fileInfoList ->
            coroutineScope.launch {
                callback.onProcessingStateChanged(true)
                
                val results = mutableListOf<Pair<Long, Media>>()
                val errors = mutableListOf<String>()
                var completedCount = 0
                
                fileInfoList.forEach { fileInfo ->
                    val mimeType = fileInfo.mimeType ?: ""
                    val helperConfig = MediaAdditionHelper.MediaAdditionConfig(
                        description = config.description,
                        autoConnectToActor = config.autoConnectToActor,
                        actorRole = config.actorRole ?: ""
                    )
                    
                    val callbackWrapper = object : MediaAdditionHelper.MediaAdditionCallback {
                        override fun onSuccess(mediaId: Long, media: Media) {
                            synchronized(results) {
                                results.add(Pair(mediaId, media))
                                completedCount++
                                if (completedCount == fileInfoList.size) {
                                    callback.onProcessingStateChanged(false)
                                    if (results.isNotEmpty()) {
                                        callback.onMultipleSuccess(results)
                                    }
                                    if (errors.isNotEmpty()) {
                                        callback.onError("部分文件处理失败: ${errors.joinToString(", ")}")
                                    }
                                }
                            }
                        }
                        override fun onError(error: String) {
                            synchronized(results) {
                                errors.add(error)
                                completedCount++
                                if (completedCount == fileInfoList.size) {
                                    callback.onProcessingStateChanged(false)
                                    if (results.isNotEmpty()) {
                                        callback.onMultipleSuccess(results)
                                    }
                                    if (errors.isNotEmpty()) {
                                        callback.onError("部分文件处理失败: ${errors.joinToString(", ")}")
                                    }
                                }
                            }
                        }
                        override fun onProcessingStateChanged(isProcessing: Boolean) {
                            // For multi-file processing, we don't need to propagate individual processing state changes
                            // as the main callback already handles overall processing state
                        }
                    }
                    
                    when {
                        mimeType.startsWith("video/") -> {
                            mediaManager.helper.addVideoFromFile(fileInfo, helperConfig, callbackWrapper)
                        }
                        mimeType.startsWith("image/") -> {
                            mediaManager.helper.addImageFromFile(fileInfo, helperConfig, callbackWrapper)
                        }
                        else -> {
                            callbackWrapper.onError("不支持的文件类型: ${fileInfo.fileName}")
                        }
                    }
                }
            }
        }
    } else null

    return if (config.allowMultiple && multipleMediaPickerLauncher != null) {
        // 多选模式
        {
            multipleMediaPickerLauncher.launch(
                androidx.activity.result.PickVisualMediaRequest(
                    androidx.activity.result.contract.ActivityResultContracts.PickVisualMedia.ImageAndVideo
                )
            )
        }
    } else {
        // 单选模式（原有逻辑）
        {
            mediaPickerLauncher.launch(
                androidx.activity.result.PickVisualMediaRequest(
                    androidx.activity.result.contract.ActivityResultContracts.PickVisualMedia.ImageAndVideo
                )
            )
        }
    }
}