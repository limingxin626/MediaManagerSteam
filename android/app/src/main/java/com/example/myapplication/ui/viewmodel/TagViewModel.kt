package com.example.myapplication.ui.viewmodel

import androidx.compose.foundation.lazy.grid.LazyGridState
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Tag
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

/**
 * Tag页面的ViewModel
 */
class TagViewModel(
    private val databaseManager: DatabaseManager
) : ViewModel() {

    // UI状态
    private val _uiState = MutableStateFlow(TagUiState())
    val uiState: StateFlow<TagUiState> = _uiState.asStateFlow()

    // 搜索查询
    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    // 分类筛选
    private val _selectedCategory = MutableStateFlow<String?>(null)
    val selectedCategory: StateFlow<String?> = _selectedCategory.asStateFlow()

    // LazyGrid状态
    val gridState = LazyGridState()

    // 所有标签
    private val allTags = databaseManager.tagRepository.getAllTags()
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = emptyList()
        )

    // 筛选后的标签
    val tags: StateFlow<List<Tag>> = combine(
        allTags,
        _searchQuery,
        _selectedCategory
    ) { tags, query, category ->
        tags.filter { tag ->
            // 按名称搜索
            val matchesSearch = query.isEmpty() || 
                tag.name.contains(query, ignoreCase = true)

            // 按分类筛选
            val matchesCategory = category == null || 
                tag.category == category

            matchesSearch && matchesCategory
        }
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    // 可选的分类列表
    val categories: StateFlow<List<String>> = allTags.map { tags ->
        tags.mapNotNull { it.category }
            .distinct()
            .sorted()
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5000),
        initialValue = emptyList()
    )

    /**
     * 搜索标签
     */
    fun searchTags(query: String) {
        _searchQuery.value = query
    }

    /**
     * 按分类筛选
     */
    fun filterByCategory(category: String?) {
        _selectedCategory.value = category
    }

    /**
     * 删除标签
     */
    fun deleteTag(tag: Tag) {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                databaseManager.tagRepository.deleteTag(tag)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    message = "标签删除成功"
                )
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "删除标签失败: ${e.message}"
                )
            }
        }
    }

    /**
     * 清除错误信息
     */
    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }

    /**
     * 清除提示信息
     */
    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }
}

/**
 * Tag页面的UI状态
 */
data class TagUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)