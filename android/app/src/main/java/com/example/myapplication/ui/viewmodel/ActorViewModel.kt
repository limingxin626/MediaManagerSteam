package com.example.myapplication.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Actor
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import androidx.compose.foundation.lazy.LazyListState

/**
 * 演员页面的ViewModel
 */
class ActorViewModel(private val databaseManager: DatabaseManager) : ViewModel() {
    
    private val _uiState = MutableStateFlow(ActorUiState())
    val uiState: StateFlow<ActorUiState> = _uiState.asStateFlow()
    
    private val _actors = MutableStateFlow<List<Actor>>(emptyList())
    val actors: StateFlow<List<Actor>> = _actors.asStateFlow()
    
    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()
    
    // 简化状态管理，移除未使用的过滤状态
    private val _selectedCountry = MutableStateFlow<String?>(null)
    val selectedCountry: StateFlow<String?> = _selectedCountry.asStateFlow()
    
    private val _selectedCategory = MutableStateFlow<String?>(null)
    val selectedCategory: StateFlow<String?> = _selectedCategory.asStateFlow()
    
    // 排序相关状态
    private val _sortBy = MutableStateFlow<ActorSortBy>(ActorSortBy.RATE_DESC)
    val sortBy: StateFlow<ActorSortBy> = _sortBy.asStateFlow()
    
    private val _countries = MutableStateFlow<List<String>>(emptyList())
    val countries: StateFlow<List<String>> = _countries.asStateFlow()
    
    private val _categories = MutableStateFlow<List<String>>(emptyList())
    val categories: StateFlow<List<String>> = _categories.asStateFlow()
    
    // 滚动状态管理
    val gridState = LazyListState()
    
    // 标记是否已经初始化过
    private var isInitialized = false
    
    init {
        if (!isInitialized) {
            loadActors()
            loadFilterOptions()
            isInitialized = true
        }
    }
    
    fun loadActors() {
        // 如果已经有数据，就不重新加载(除非明确调用 refreshActors)
        if (_actors.value.isNotEmpty()) {
            return
        }
        
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                databaseManager.actorRepository.getAllActors().collect { actorList ->
                    // 应用默认排序
                    val sortedList = when (_sortBy.value) {
                        ActorSortBy.NAME_ASC -> actorList.sortedBy { it.name }
                        ActorSortBy.NAME_DESC -> actorList.sortedByDescending { it.name }
                        else -> actorList.sortedBy { it.name }
                    }
                    _actors.value = sortedList
                    _uiState.value = _uiState.value.copy(isLoading = false, error = null)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "加载演员失败: ${e.message}"
                )
            }
        }
    }
    
    fun searchActors(query: String) {
        _searchQuery.value = query
        applyFilters() // 统一使用筛选逻辑
    }
    
    // 简化过滤方法，仅保留搜索功能
    fun filterByCountry(country: String?) {
        _selectedCountry.value = country
        applyFilters()
    }
    
    fun filterByCategory(category: String?) {
        _selectedCategory.value = category
        applyFilters()
    }
    
    fun sortBy(sortBy: ActorSortBy) {
        _sortBy.value = sortBy
        applyFilters()
    }
    
    private fun applyFilters() {
        viewModelScope.launch {
            try {
                val searchQuery = _searchQuery.value
                
                // 获取所有演员数据
                databaseManager.actorRepository.getAllActors().collect { allActors ->
                    var filteredActors = allActors
                    
                    // 应用搜索筛选
                    if (searchQuery.isNotBlank()) {
                        filteredActors = filteredActors.filter { 
                            it.name.contains(searchQuery, ignoreCase = true) 
                        }
                    }
                    
                    // 应用排序
                    filteredActors = when (_sortBy.value) {
                        ActorSortBy.NAME_ASC -> filteredActors.sortedBy { it.name }
                        ActorSortBy.NAME_DESC -> filteredActors.sortedByDescending { it.name }
                        else -> filteredActors.sortedBy { it.name }
                    }
                    
                    _actors.value = filteredActors
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "筛选失败: ${e.message}")
            }
        }
    }
    
    private fun loadFilterOptions() {
        // 简化实现，移除对不存在方法的引用
        viewModelScope.launch {
            try {
                // 清空国家和分类列表
                _countries.value = emptyList()
                _categories.value = emptyList()
            } catch (e: Exception) {
                // 静默失败，不影响主要功能
            }
        }
    }
    
    fun deleteActor(actor: Actor) {
        viewModelScope.launch {
            try {
                databaseManager.actorRepository.deleteActor(actor)
                _uiState.value = _uiState.value.copy(message = "删除演员成功")
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
    
    fun addActor(actor: Actor) {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                databaseManager.actorRepository.insertActor(actor)
                _uiState.value = _uiState.value.copy(
                    isLoading = false, 
                    message = "添加演员成功"
                )
                // 强制刷新列表
                forceRefresh()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "添加演员失败: ${e.message}"
                )
            }
        }
    }
    
    fun updateActor(actor: Actor) {
        viewModelScope.launch {
            try {
                _uiState.value = _uiState.value.copy(isLoading = true)
                databaseManager.actorRepository.updateActor(actor)
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    message = "更新演员成功"
                )
                // 强制刷新列表
                forceRefresh()
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "更新演员失败: ${e.message}"
                )
            }
        }
    }
    
    private fun forceRefresh() {
        viewModelScope.launch {
            try {
                databaseManager.actorRepository.getAllActors().collect { actorList ->
                    _actors.value = actorList
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(error = "刷新失败: ${e.message}")
            }
        }
    }
    
    suspend fun getActorById(id: Long): Actor? {
        return databaseManager.actorRepository.getActorById(id)
    }
    
    fun refreshActors() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            try {
                databaseManager.actorRepository.getAllActors().collect { actorList ->
                    _actors.value = actorList
                    _uiState.value = _uiState.value.copy(isLoading = false, error = null)
                }
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "刷新演员失败: ${e.message}"
                )
            }
        }
    }
}

/**
 * 演员页面UI状态
 */
data class ActorUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)

/**
 * 演员排序方式
 */
enum class ActorSortBy(val displayName: String) {
    NAME_ASC("姓名升序"),
    NAME_DESC("姓名降序"),
    RATE_ASC("评分升序"),
    RATE_DESC("评分降序")
}

