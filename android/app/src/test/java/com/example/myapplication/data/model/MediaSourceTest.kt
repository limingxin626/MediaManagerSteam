package com.example.myapplication.data.model

import com.example.myapplication.data.database.entities.Media
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MediaSourceTest {
    @Test
    fun mediaStoreSourcePrefersContentUriAndFallsBackToRemote() {
        val media = Media(
            sourceType = Media.SOURCE_MEDIA_STORE,
            contentUri = "content://media/1",
            remoteMediaUrl = "https://example/media/1",
            remoteThumbnailUrl = "https://example/thumb/1",
            fileHash = "hash"
        )

        assertEquals("content://media/1", media.primaryMediaPath())
        assertEquals("content://media/1", media.primaryThumbnailPath())
        assertEquals("https://example/media/1", media.primaryMediaPath(contentUriAvailable = false))
        assertEquals("https://example/thumb/1", media.primaryThumbnailPath(contentUriAvailable = false))
    }

    @Test
    fun unavailableMediaWithoutRemoteHasNoPath() {
        val media = Media(
            sourceType = Media.SOURCE_MEDIA_STORE,
            contentUri = "content://media/missing",
            fileHash = "hash"
        )

        assertNull(media.primaryMediaPath(contentUriAvailable = false))
        assertNull(media.primaryThumbnailPath(contentUriAvailable = false))
    }
}
