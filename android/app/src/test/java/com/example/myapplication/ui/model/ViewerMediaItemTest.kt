package com.example.myapplication.ui.model

import com.example.myapplication.data.database.entities.Media
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ViewerMediaItemTest {
    @Test
    fun roomMediaMapsViewerFields() {
        val item = Media(
            id = 7,
            fileHash = "hash",
            localMediaPath = "/media/video.mp4",
            localThumbnailPath = "/thumb/video.webp",
            mimeType = "video/mp4",
            starred = true
        ).toViewerMediaItem()

        assertEquals("room:7", item.key)
        assertEquals("/media/video.mp4", item.mediaUri)
        assertEquals("/thumb/video.webp", item.thumbnailUri)
        assertTrue(item.isVideo)
        assertEquals(true, item.starred)
    }

    @Test
    fun neutralItemDetectsImageWithoutStarCapability() {
        val item = ViewerMediaItem(
            key = "system:image:1",
            mediaUri = "content://media/external/images/media/1",
            thumbnailUri = null,
            mimeType = "image/jpeg"
        )

        assertFalse(item.isVideo)
        assertNull(item.starred)
    }
}
