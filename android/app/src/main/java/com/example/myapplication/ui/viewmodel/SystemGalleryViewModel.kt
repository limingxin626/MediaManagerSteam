package com.example.myapplication.ui.viewmodel

import android.content.Context
import androidx.compose.foundation.lazy.grid.LazyGridState
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.data.repository.SystemMediaRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * 系统相册页面的ViewModel
 */
class SystemGalleryViewModel(context: Context) : ViewModel() {

    private val systemMediaRepository = SystemMediaRepository(context)

    private val _uiState = MutableStateFlow(SystemGalleryUiState())
    val uiState: StateFlow<SystemGalleryUiState> = _uiState.asStateFlow()

    private val _mediaList = MutableStateFlow<List<SystemMedia>>(emptyList())
    val mediaList: StateFlow<List<SystemMedia>> = _mediaList.asStateFlow()

    private val _mediaByFolder = MutableStateFlow<Map<String, List<SystemMedia>>>(emptyMap())
    val mediaByFolder: StateFlow<Map<String, List<SystemMedia>>> = _mediaByFolder.asStateFlow()

    private val _filterType = MutableStateFlow(MediaFilterType.ALL)
    val filterType: StateFlow<MediaFilterType> = _filterType.asStateFlow()

    private val _viewMode = MutableStateFlow(ViewMode.GRID)
    val viewMode: StateFlow<ViewMode> = _viewMode.asStateFlow()

    private val _expandedFolders = MutableStateFlow<Set<String>>(emptySet())
    val expandedFolders: StateFlow<Set<String>> = _expandedFolders.asStateFlow()

    private val _selectedMedia = MutableStateFlow<Set<SystemMedia>>(emptySet())
    val selectedMedia: StateFlow<Set<SystemMedia>> = _selectedMedia.asStateFlow()

    private val _isSelectionMode = MutableStateFlow(false)
    val isSelectionMode: StateFlow<Boolean> = _isSelectionMode.asStateFlow()

    // 网格滚动状态
    val gridState = LazyGridState()

    // 权限状态
    private val _hasPermission = MutableStateFlow(false)
    val hasPermission: StateFlow<Boolean> = _hasPermission.asStateFlow()

    init {
        // 初始时不自动加载，等待权限授予
    }

    /**
     * 设置权限状态并加载数据
     */
    fun setPermissionGranted(granted: Boolean) {
        _hasPermission.value = granted
        if (granted) {
            loadSystemMedia()
        } else {
            _mediaList.value = emptyList()
            _uiState.value = _uiState.value.copy(
                isLoading = false,
                error = "需要存储权限才能访问设备中的媒体文件"
            )
        }
    }

    /**
     * 加载系统媒体
     */
    fun loadSystemMedia() {
        if (!_hasPermission.value) {
            _uiState.value = _uiState.value.copy(
                error = "没有存储权限"
            )
            return
        }

        // 如果已经在加载或已有数据，避免重复加载
        if (_uiState.value.isLoading ||
            (_mediaList.value.isNotEmpty() || _mediaByFolder.value.isNotEmpty())
        ) {
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                if (_viewMode.value == ViewMode.FOLDER) {
                    // 文件夹模式：按文件夹分组加载
                    systemMediaRepository.getMediaByBucket().collect { mediaByFolder ->
                        val filteredByFolder = when (_filterType.value) {
                            MediaFilterType.ALL -> mediaByFolder
                            MediaFilterType.IMAGES -> mediaByFolder.mapValues { (_, mediaList) ->
                                mediaList.filter { it.isImage }
                            }.filter { it.value.isNotEmpty() }

                            MediaFilterType.VIDEOS -> mediaByFolder.mapValues { (_, mediaList) ->
                                mediaList.filter { it.isVideo }
                            }.filter { it.value.isNotEmpty() }
                        }

                        _mediaByFolder.value = filteredByFolder
                        val totalCount = filteredByFolder.values.sumOf { it.size }
                        _uiState.value = _uiState.value.copy(
                            isLoading = false,
                            mediaCount = totalCount,
                            folderCount = filteredByFolder.size
                        )
                    }
                } else {
                    // 网格模式：直接加载所有媒体
                    when (_filterType.value) {
                        MediaFilterType.ALL -> {
                            systemMediaRepository.getAllSystemMedia().collect { mediaList ->
                                _mediaList.value = mediaList
                                _uiState.value = _uiState.value.copy(
                                    isLoading = false,
                                    mediaCount = mediaList.size
                                )
                            }
                        }

                        MediaFilterType.IMAGES -> {
                            systemMediaRepository.getImages().collect { mediaList ->
                                _mediaList.value = mediaList
                                _uiState.value = _uiState.value.copy(
                                    isLoading = false,
                                    mediaCount = mediaList.size
                                )
                            }
                        }

                        MediaFilterType.VIDEOS -> {
                            systemMediaRepository.getVideos().collect { mediaList ->
                                _mediaList.value = mediaList
                                _uiState.value = _uiState.value.copy(
                                    isLoading = false,
                                    mediaCount = mediaList.size
                                )
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "加载媒体失败: ${e.message}"
                )
            }
        }
    }

    /**
     * 切换媒体类型筛选
     */
    fun setFilterType(filterType: MediaFilterType) {
        if (_filterType.value != filterType) {
            _filterType.value = filterType
            loadSystemMedia()
        }
    }

    /**
     * 切换视图模式
     */
    fun setViewMode(viewMode: ViewMode) {
        if (_viewMode.value != viewMode) {
            _viewMode.value = viewMode
            loadSystemMedia()
        }
    }

    /**
     * 切换文件夹展开状态
     */
    fun toggleFolderExpansion(folderName: String) {
        val currentExpanded = _expandedFolders.value.toMutableSet()
        if (currentExpanded.contains(folderName)) {
            currentExpanded.remove(folderName)
        } else {
            currentExpanded.add(folderName)
        }
        _expandedFolders.value = currentExpanded
    }

    /**
     * 展开所有文件夹
     */
    fun expandAllFolders() {
        _expandedFolders.value = _mediaByFolder.value.keys.toSet()
    }

    /**
     * 折叠所有文件夹
     */
    fun collapseAllFolders() {
        _expandedFolders.value = emptySet()
    }

    /**
     * 开启选择模式
     */
    fun enterSelectionMode() {
        _isSelectionMode.value = true
        _selectedMedia.value = emptySet()
    }

    /**
     * 退出选择模式
     */
    fun exitSelectionMode() {
        _isSelectionMode.value = false
        _selectedMedia.value = emptySet()
    }

    /**
     * 切换媒体选择状态
     */
    fun toggleMediaSelection(media: SystemMedia) {
        val currentSelection = _selectedMedia.value.toMutableSet()
        if (currentSelection.contains(media)) {
            currentSelection.remove(media)
        } else {
            currentSelection.add(media)
        }
        _selectedMedia.value = currentSelection

        // 如果没有选中任何项，自动退出选择模式
        if (currentSelection.isEmpty()) {
            _isSelectionMode.value = false
        }
    }

    /**
     * 全选/取消全选
     */
    fun toggleSelectAll() {
        val currentSelection = _selectedMedia.value
        if (currentSelection.size == _mediaList.value.size) {
            // 当前全选，执行取消全选
            _selectedMedia.value = emptySet()
            _isSelectionMode.value = false
        } else {
            // 执行全选
            _selectedMedia.value = _mediaList.value.toSet()
        }
    }

    /**
     * 专门为文件夹视图加载数据
     */
    fun loadFolderData() {
        if (!_hasPermission.value) {
            _uiState.value = _uiState.value.copy(
                error = "没有存储权限"
            )
            return
        }

        // 如果已经在加载，避免重复加载
        if (_uiState.value.isLoading) {
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true, error = null)

            try {
                // 文件夹模式：按文件夹分组加载
                systemMediaRepository.getMediaByBucket().collect { mediaByFolder ->
                    val filteredByFolder = when (_filterType.value) {
                        MediaFilterType.ALL -> mediaByFolder
                        MediaFilterType.IMAGES -> mediaByFolder.mapValues { (_, mediaList) ->
                            mediaList.filter { it.isImage }
                        }.filter { it.value.isNotEmpty() }

                        MediaFilterType.VIDEOS -> mediaByFolder.mapValues { (_, mediaList) ->
                            mediaList.filter { it.isVideo }
                        }.filter { it.value.isNotEmpty() }
                    }

                    _mediaByFolder.value = filteredByFolder
                    val totalCount = filteredByFolder.values.sumOf { it.size }
                    _uiState.value = _uiState.value.copy(
                        isLoading = false,
                        mediaCount = totalCount,
                        folderCount = filteredByFolder.size
                    )
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "加载媒体失败: ${e.message}"
                )
            }
        }
    }

    /**
     * 刷新数据
     */
    fun refresh() {
        if (_viewMode.value == ViewMode.FOLDER || _mediaByFolder.value.isNotEmpty()) {
            // 如果当前是文件夹模式或已有文件夹数据，刷新文件夹数据
            _mediaByFolder.value = emptyMap()
            loadFolderData()
        } else {
            // 否则刷新网格数据
            _mediaList.value = emptyList()
            loadSystemMedia()
        }
    }

    /**
     * 清除错误信息
     */
    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    /**
     * 清除消息
     */
    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }

    /**
     * 获取当前选中媒体的统计信息
     */
    fun getSelectionInfo(): SelectionInfo {
        val selected = _selectedMedia.value
        val imageCount = selected.count { it.isImage }
        val videoCount = selected.count { it.isVideo }
        val totalSize = selected.sumOf { it.size }

        return SelectionInfo(
            totalCount = selected.size,
            imageCount = imageCount,
            videoCount = videoCount,
            totalSize = totalSize
        )
    }
}

/**
 * 媒体筛选类型
 */
enum class MediaFilterType(val displayName: String) {
    ALL("全部"),
    IMAGES("图片"),
    VIDEOS("视频")
}

/**
 * 视图模式
 */
enum class ViewMode(val displayName: String) {
    GRID("网格视图"),
    FOLDER("文件夹视图")
}

/**
 * 选择信息
 */
data class SelectionInfo(
    val totalCount: Int,
    val imageCount: Int,
    val videoCount: Int,
    val totalSize: Long
) {
    fun getFormattedSize(): String {
        return when {
            totalSize < 1024 -> "${totalSize}B"
            totalSize < 1024 * 1024 -> "${totalSize / 1024}KB"
            totalSize < 1024 * 1024 * 1024 -> "${totalSize / (1024 * 1024)}MB"
            else -> "${totalSize / (1024 * 1024 * 1024)}GB"
        }
    }
}

/**
 * 系统相册页面的UI状态
 */
data class SystemGalleryUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null,
    val mediaCount: Int = 0,
    val folderCount: Int = 0
)