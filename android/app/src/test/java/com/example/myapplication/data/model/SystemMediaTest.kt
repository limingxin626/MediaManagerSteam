package com.example.myapplication.data.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class SystemMediaTest {
    @Test
    fun stableKeySeparatesImageAndVideoIds() {
        val imageKey = systemMediaStableKey(42L, "image/jpeg")
        val videoKey = systemMediaStableKey(42L, "video/mp4")

        assertEquals("image:42", imageKey)
        assertEquals("video:42", videoKey)
        assertNotEquals(imageKey, videoKey)
    }
}
