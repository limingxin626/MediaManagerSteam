package com.example.myapplication.ui.model

import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.model.SystemMedia

data class ViewerMediaItem(
    val key: String,
    val mediaUri: String?,
    val thumbnailUri: String?,
    val mimeType: String?,
    val fallbackMediaUri: String? = null,
    val fallbackThumbnailUri: String? = null,
    val starred: Boolean? = null
) {
    val isVideo: Boolean
        get() = mimeType?.startsWith("video/") == true
}

fun Media.toViewerMediaItem() = ViewerMediaItem(
    key = "room:$id",
    mediaUri = filePath,
    thumbnailUri = thumbnailPath,
    mimeType = mimeType,
    fallbackMediaUri = remoteMediaUrl,
    fallbackThumbnailUri = remoteThumbnailUrl ?: remoteMediaUrl,
    starred = starred
)

fun SystemMedia.toViewerMediaItem(starred: Boolean? = null) = ViewerMediaItem(
    key = "system:$stableKey",
    mediaUri = uri.toString(),
    thumbnailUri = null,
    mimeType = mimeType,
    starred = starred
)
