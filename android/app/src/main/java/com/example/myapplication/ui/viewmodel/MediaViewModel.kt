package com.example.myapplication.ui.viewmodel

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.myapplication.data.DatabaseManager
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.model.SystemMedia
import com.example.myapplication.data.repository.SystemMediaRepository
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/** 系统媒体页面的 ViewModel。 */
class MediaViewModel(
    context: Context,
    private val databaseManager: DatabaseManager
) : ViewModel() {

    private val repository = SystemMediaRepository(context.applicationContext)

    private val _uiState = MutableStateFlow(MediaUiState())
    val uiState: StateFlow<MediaUiState> = _uiState.asStateFlow()

    private val _mediaList = MutableStateFlow<List<SystemMedia>>(emptyList())
    val mediaList: StateFlow<List<SystemMedia>> = _mediaList.asStateFlow()

    private var loadJob: Job? = null

    fun updatePermissions(canReadImages: Boolean, canReadVideos: Boolean) {
        val permissionsChanged = _uiState.value.canReadImages != canReadImages ||
            _uiState.value.canReadVideos != canReadVideos
        _uiState.value = _uiState.value.copy(
            canReadImages = canReadImages,
            canReadVideos = canReadVideos,
            permissionDenied = !canReadImages && !canReadVideos,
            error = null
        )
        if (canReadImages || canReadVideos) {
            if (permissionsChanged || _mediaList.value.isEmpty()) refreshMedia()
        } else {
            loadJob?.cancel()
            _mediaList.value = emptyList()
            _uiState.value = _uiState.value.copy(isLoading = false)
        }
    }

    fun insertMedia(media: Media) {
        viewModelScope.launch {
            databaseManager.mediaRepository.insertMedia(media)
        }
    }

    fun refreshMedia() {
        val state = _uiState.value
        if (!state.canReadImages && !state.canReadVideos) return

        loadJob?.cancel()
        loadJob = viewModelScope.launch {
            _uiState.value = _uiState.value.copy(
                isLoading = _mediaList.value.isEmpty(),
                error = null
            )
            try {
                repository.getAccessibleSystemMedia(
                    canReadImages = state.canReadImages,
                    canReadVideos = state.canReadVideos
                ).collect { media ->
                    _mediaList.value = media
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
