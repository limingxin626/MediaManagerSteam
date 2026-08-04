package com.example.myapplication.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.MessageWithDetails
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class CollectionGroupItem(
    val collectionId: Long?,
    val name: String,
    val messageCount: Int,
    val lastMessage: MessageWithDetails?,
    val coverPath: String?
)

/**
 * 合集分组页面的ViewModel
 */
class CollectionViewModel(private val databaseManager: DatabaseManager) : ViewModel() {

    private val _groups = MutableStateFlow<List<CollectionGroupItem>>(emptyList())
    val groups: StateFlow<List<CollectionGroupItem>> = _groups.asStateFlow()

    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _uiState = MutableStateFlow(CollectionUiState())
    val uiState: StateFlow<CollectionUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            databaseManager.collectionRepository.getAllCollections().collect { collections ->
                loadGroups(collections)
            }
        }
    }

    private suspend fun loadGroups(collections: List<com.example.myapplication.data.database.entities.Collection>) {
        _isLoading.value = true
        val messageRepository = databaseManager.messageRepository
        val groups = mutableListOf<CollectionGroupItem>()

        // "全部" group
        val totalCount = messageRepository.getTotalMessageCount()
        val lastMessage = messageRepository.getLastMessage()
        groups.add(
            CollectionGroupItem(
                collectionId = null,
                name = "全部",
                messageCount = totalCount,
                lastMessage = lastMessage,
                coverPath = null
            )
        )

        // Each collection as a group
        for (collection in collections) {
            val count = messageRepository.getMessageCountByCollection(collection.id)
            val collectionLastMessage =
                if (count > 0) messageRepository.getLastMessageByCollection(collection.id) else null
            groups.add(
                CollectionGroupItem(
                    collectionId = collection.id,
                    name = collection.name,
                    messageCount = count,
                    lastMessage = collectionLastMessage,
                    coverPath = collection.coverPath
                )
            )
        }

        // "全部" stays first, rest sorted by message count descending
        val allGroup = groups.first()
        val collectionGroups = groups.drop(1).sortedByDescending { it.messageCount }
        _groups.value = listOf(allGroup) + collectionGroups
        _isLoading.value = false
    }

    fun clearMessage() {
        _uiState.value = _uiState.value.copy(message = null)
    }

    fun clearError() {
        _uiState.value = _uiState.value.copy(error = null)
    }
}

/**
 * 合集页面UI状态
 */
data class CollectionUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)
