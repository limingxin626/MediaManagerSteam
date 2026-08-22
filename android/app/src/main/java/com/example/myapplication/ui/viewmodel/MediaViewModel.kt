package com.example.myapplication.ui.viewmodel

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.Tag
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.data.repository.SystemMediaRepository
import com.example.myapplication.ui.model.SystemMediaWithMetadata
import com.example.myapplication.ui.model.filterSystemMedia
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

class MediaViewModel(
    context: Context,
    private val databaseManager: DatabaseManager
) : ViewModel() {
    private val mediaStoreRepository = SystemMediaRepository(context.applicationContext)
    private val metadataRepository = databaseManager.systemMediaMetadataRepository

    private val _uiState = MutableStateFlow(MediaUiState())
    val uiState: StateFlow<MediaUiState> = _uiState.asStateFlow()

    private val _systemMedia = MutableStateFlow<List<SystemMedia>>(emptyList())
    val allSystemMedia: StateFlow<List<SystemMedia>> = _systemMedia.asStateFlow()

    private val _starredOnly = MutableStateFlow(false)
    val starredOnly: StateFlow<Boolean> = _starredOnly.asStateFlow()

    private val _selectedTagId = MutableStateFlow<Long?>(null)
    val selectedTagId: StateFlow<Long?> = _selectedTagId.asStateFlow()

    val allTags: StateFlow<List<Tag>> = databaseManager.tagRepository.getAllTags()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    val metadata = metadataRepository.metadata
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())
    val tagLinks = metadataRepository.tagLinks
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val allMediaWithMetadata: StateFlow<List<SystemMediaWithMetadata>> = combine(
        _systemMedia,
        metadata,
        tagLinks,
        allTags
    ) { media, metadata, links, tags ->
        val metadataByKey = metadata.associateBy { it.stableKey }
        val tagsById = tags.associateBy { it.id }
        val tagIdsByKey = links.groupBy { it.systemMediaKey }
        media.map { item ->
            SystemMediaWithMetadata(
                media = item,
                starred = metadataByKey[item.stableKey]?.starred == true,
                tags = tagIdsByKey[item.stableKey]
                    .orEmpty()
                    .mapNotNull { tagsById[it.tagId] }
            )
        }
    }.flowOn(Dispatchers.Default)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    val mediaList: StateFlow<List<SystemMediaWithMetadata>> = combine(
        allMediaWithMetadata,
        _starredOnly,
        _selectedTagId
    ) { items, starredOnly, tagId ->
        filterSystemMedia(items, starredOnly, tagId)
    }.flowOn(Dispatchers.Default)
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    private var loadJob: Job? = null

    fun updatePermissions(canReadImages: Boolean, canReadVideos: Boolean) {
        val changed = _uiState.value.canReadImages != canReadImages ||
            _uiState.value.canReadVideos != canReadVideos
        _uiState.value = _uiState.value.copy(
            canReadImages = canReadImages,
            canReadVideos = canReadVideos,
            permissionDenied = !canReadImages && !canReadVideos,
            error = null
        )
        if (canReadImages || canReadVideos) {
            if (changed || _systemMedia.value.isEmpty()) refreshMedia()
        } else {
            loadJob?.cancel()
            _systemMedia.value = emptyList()
            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    fun toggleStarred(item: SystemMediaWithMetadata) {
        viewModelScope.launch {
            metadataRepository.toggleStarred(
                stableKey = item.media.stableKey,
                contentUri = item.media.uri.toString()
            )
        }
    }

    fun metadataFor(media: SystemMedia): SystemMediaWithMetadata {
        val metadataByKey = metadata.value.associateBy { it.stableKey }
        val tagsById = allTags.value.associateBy { it.id }
        val itemTags = tagLinks.value
            .asSequence()
            .filter { it.systemMediaKey == media.stableKey }
            .mapNotNull { tagsById[it.tagId] }
            .toList()
        return SystemMediaWithMetadata(
            media = media,
            starred = metadataByKey[media.stableKey]?.starred == true,
            tags = itemTags
        )
    }

    fun setTags(item: SystemMediaWithMetadata, tags: List<Tag>) {
        viewModelScope.launch {
            metadataRepository.setTags(
                stableKey = item.media.stableKey,
                contentUri = item.media.uri.toString(),
                tagIds = tags.mapTo(mutableSetOf()) { it.id }
            )
        }
    }

    fun toggleStarredFilter() {
        _starredOnly.value = !_starredOnly.value
    }

    fun selectTagFilter(tagId: Long?) {
        _selectedTagId.value = tagId
    }

    fun insertMedia(media: Media) {
        viewModelScope.launch { databaseManager.mediaRepository.insertMedia(media) }
    }

    fun refreshMedia() {
        val state = _uiState.value
        if (!state.canReadImages && !state.canReadVideos) return
        loadJob?.cancel()
        loadJob = viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = _systemMedia.value.isEmpty(),
                error = null
            )
            try {
                mediaStoreRepository.getAccessibleSystemMedia(
                    canReadImages = state.canReadImages,
                    canReadVideos = state.canReadVideos
                ).collect { media ->
                    _systemMedia.value = media
                    _uiState.value = _uiState.value.copy(isLoading = false, error = null)
                }
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    error = "加载系统媒体失败: ${e.message ?: "未知错误"}"
                )
            }
        }
    }
}

data class MediaUiState(
    val isLoading: Boolean = false,
    val canReadImages: Boolean = false,
    val canReadVideos: Boolean = false,
    val permissionDenied: Boolean = true,
    val error: String? = null
)
