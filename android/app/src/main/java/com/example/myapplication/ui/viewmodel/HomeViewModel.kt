package com.example.myapplication.ui.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.database.entities.MessageWithDetails
import com.example.myapplication.data.repository.MessageRepository
import com.example.myapplication.data.repository.TagRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

data class GroupItem(
    val tagId: Long?,
    val name: String,
    val messageCount: Int,
    val lastMessage: MessageWithDetails?,
    val color: String?
)

class HomeViewModel(
    private val tagRepository: TagRepository,
    private val messageRepository: MessageRepository
) : ViewModel() {

    private val _groups = MutableStateFlow<List<GroupItem>>(emptyList())
    val groups: StateFlow<List<GroupItem>> = _groups.asStateFlow()

    private val _isLoading = MutableStateFlow(true)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()

    init {
        viewModelScope.launch {
            tagRepository.getAllTags().collect { tags ->
                loadGroups(tags)
            }
        }
    }

    private suspend fun loadGroups(tags: List<com.example.myapplication.data.database.entities.Tag>) {
        _isLoading.value = true
        val groups = mutableListOf<GroupItem>()

        // "全部" group
        val totalCount = messageRepository.getTotalMessageCount()
        val lastMessage = messageRepository.getLastMessage()
        groups.add(
            GroupItem(
                tagId = null,
                name = "全部",
                messageCount = totalCount,
                lastMessage = lastMessage,
                color = null
            )
        )

        // Each tag as a group
        for (tag in tags) {
            val count = tagRepository.getMessageCountForTag(tag.id)
            val tagLastMessage = if (count > 0) messageRepository.getLastMessageForTag(tag.id) else null
            groups.add(
                GroupItem(
                    tagId = tag.id,
                    name = tag.name,
                    messageCount = count,
                    lastMessage = tagLastMessage,
                    color = tag.color
                )
            )
        }

        // "全部" stays first, rest sorted by message count descending
        val allGroup = groups.first()
        val tagGroups = groups.drop(1).sortedByDescending { it.messageCount }
        _groups.value = listOf(allGroup) + tagGroups
        _isLoading.value = false
    }

    fun refresh() {
        viewModelScope.launch {
            tagRepository.getAllTags().collect { tags ->
                loadGroups(tags)
            }
        }
    }
}
