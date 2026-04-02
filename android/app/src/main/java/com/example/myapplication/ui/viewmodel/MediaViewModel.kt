package com.example.myapplication.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import androidx.compose.foundation.lazy.staggeredgrid.LazyStaggeredGridState

/**
 * 媒体页面的ViewModel
 */
class MediaViewModel(private val databaseManager: DatabaseManager) : ViewModel() {
    
    private val _uiState = MutableStateFlow(MediaUiState())
    val uiState: StateFlow<MediaUiState> = _uiState.asStateFlow()
    
    private val _mediaList = MutableStateFlow<List<Media>>(emptyList())
    val mediaList: StateFlow<List<Media>> = _mediaList.asStateFlow()
    
    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()
    
    private val _sortOrder = MutableStateFlow("createdAt")
    val sortOrder: StateFlow<String> = _sortOrder.asStateFlow()
    
    private val _selectedGenre = MutableStateFlow<String?>(null)
    val selectedGenre: StateFlow<String?> = _selectedGenre.asStateFlow()
    
    private val _genres = MutableStateFlow<List<String>>(emptyList())
    val genres: StateFlow<List<String>> = _genres.asStateFlow()
    
    // 滚动状态管理 - 瀑布流布局
    val staggeredGridState = LazyStaggeredGridState()
    
    // 标记是否已经初始化过
    private var isInitialized = false
    
    init {
        if (!isInitialized) {
            loadMedia()
            loadFilterOptions()
            isInitialized = true
        }
    }
    
    fun loadMedia() {
        // 如果已经有数据且没有搜索和筛选，就不重新加载
        if (_mediaList.value.isNotEmpty() && 
            _searchQuery.value.isEmpty() && 
            _selectedGenre.value == null) {
            return
        }
        
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                databaseManager.mediaRepository.getAllMedia().collect { mediaList ->
                    _mediaList.value = mediaList
                    _uiState.value = _uiState.value.copy(isLoading = false, error = null)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "加载媒体失败: ${e.message}"
                )
            }
        }
    }
    
    fun searchMedia(query: String) {
        _searchQuery.value = query
        applyFilters() // 统一使用筛选逻辑
    }
    
    fun filterByGenre(genre: String?) {
        _selectedGenre.value = genre
        applyFilters()
    }
    
    fun setSortOrder(sortOrder: String) {
        _sortOrder.value = sortOrder
        applyFilters()
    }
    
    private fun applyFilters() {
        viewModelScope.launch {
            try {
                val searchQuery = _searchQuery.value
                val sortOrder = _sortOrder.value
                
                // 获取所有媒体数据
                databaseManager.mediaRepository.getAllMedia().collect { allMedia ->
                    var filteredMedia = allMedia
                    
                    // 应用搜索筛选
                    if (searchQuery.isNotBlank()) {
                        filteredMedia = filteredMedia.filter { 
                            (it.localMediaPath?.contains(searchQuery, ignoreCase = true) ?: false) ||
                            (it.remoteMediaUrl?.contains(searchQuery, ignoreCase = true) ?: false)
                        }
                    }
                    
                    // 应用排序
                    val sortedMedia = when (sortOrder) {
                        "createdAt" -> filteredMedia.sortedByDescending { it.createdAt }
                        "rating" -> filteredMedia.sortedByDescending { it.rating }
                        "duration" -> filteredMedia.sortedByDescending { it.durationMs ?: 0L }
                        "fileSize" -> filteredMedia.sortedByDescending { it.fileSize ?: 0L }
                        else -> filteredMedia.sortedByDescending { it.createdAt }
                    }
                    
                    _mediaList.value = sortedMedia
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "筛选失败: ${e.message}")
            }
        }
    }
    
    private fun loadFilterOptions() {
        viewModelScope.launch {
            try {
                // 使用新的标签系统获取所有标签
                databaseManager.tagRepository.getAllTags().collect { tagList ->
                    _genres.value = tagList.map { it.name }.sorted()
                }
            } catch (e: Exception) {
                // 静默失败，不影响主要功能
            }
        }
    }
    
    fun addMedia(media: Media) {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                databaseManager.mediaRepository.insertMedia(media)
                _uiState.value = _uiState.value.copy(
                    isLoading = false, 
                    message = "添加媒体成功"
                )
                // 刷新列表
                loadMedia()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "添加媒体失败: ${e.message}"
                )
            }
        }
    }
    
    fun updateMedia(media: Media) {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                databaseManager.mediaRepository.updateMedia(media)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    message = "更新媒体成功"
                )
                // 刷新列表
                loadMedia()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "更新媒体失败: ${e.message}"
                )
            }
        }
    }
    
    fun deleteMedia(media: Media) {
        viewModelScope.launch {
            try {
                databaseManager.mediaRepository.deleteMedia(media)
                _uiState.value = _uiState.value.copy(message = "删除媒体成功")
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "删除失败: ${e.message}")
            }
        }
    }
    
    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }
    
    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
    
    suspend fun getMediaById(id: Long): Media? {
        return databaseManager.mediaRepository.getMediaById(id)
    }
    

    fun insertMedia(media: Media) {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                databaseManager.mediaRepository.insertMedia(media)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    message = "创建媒体记录成功"
                )
                // 刷新列表
                loadMedia()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "创建媒体记录失败: ${e.message}"
                )
            }
        }
    }
    
    fun refreshMedia() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                databaseManager.mediaRepository.getAllMedia().collect { mediaList ->
                    _mediaList.value = mediaList
                    _uiState.value = _uiState.value.copy(isLoading = false, error = null)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "刷新媒体失败: ${e.message}"
                )
            }
        }
    }
}

/**
 * 媒体页面UI状态
 */
data class MediaUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)