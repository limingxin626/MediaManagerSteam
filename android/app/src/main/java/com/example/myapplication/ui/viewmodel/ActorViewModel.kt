package com.example.myapplication.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.MessageWithDetails
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class ActorGroupItem(
    val actorId: Long?,
    val name: String,
    val messageCount: Int,
    val lastMessage: MessageWithDetails?,
    val avatarPath: String?
)

/**
 * 演员分组页面的ViewModel
 */
class ActorViewModel(private val databaseManager: DatabaseManager) : ViewModel() {

    private val _groups = MutableStateFlow<List<ActorGroupItem>>(emptyList())
    val groups: StateFlow<List<ActorGroupItem>> = _groups.asStateFlow()

    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    private val _uiState = MutableStateFlow(ActorUiState())
    val uiState: StateFlow<ActorUiState> = _uiState.asStateFlow()

    init {
        viewModelScope.launch {
            databaseManager.actorRepository.getAllActors().collect { actors ->
                loadGroups(actors)
            }
        }
    }

    private suspend fun loadGroups(actors: List<com.example.myapplication.data.database.entities.Actor>) {
        _isLoading.value = true
        val messageRepository = databaseManager.messageRepository
        val groups = mutableListOf<ActorGroupItem>()

        // "全部" group
        val totalCount = messageRepository.getTotalMessageCount()
        val lastMessage = messageRepository.getLastMessage()
        groups.add(
            ActorGroupItem(
                actorId = null,
                name = "全部",
                messageCount = totalCount,
                lastMessage = lastMessage,
                avatarPath = null
            )
        )

        // Each actor as a group
        for (actor in actors) {
            val count = messageRepository.getMessageCountByActor(actor.id)
            val actorLastMessage = if (count > 0) messageRepository.getLastMessageByActor(actor.id) else null
            groups.add(
                ActorGroupItem(
                    actorId = actor.id,
                    name = actor.name,
                    messageCount = count,
                    lastMessage = actorLastMessage,
                    avatarPath = actor.avatarPath
                )
            )
        }

        // "全部" stays first, rest sorted by message count descending
        val allGroup = groups.first()
        val actorGroups = groups.drop(1).sortedByDescending { it.messageCount }
        _groups.value = listOf(allGroup) + actorGroups
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
 * 演员页面UI状态
 */
data class ActorUiState(
    val isLoading: Boolean = false,
    val error: String? = null,
    val message: String? = null
)
