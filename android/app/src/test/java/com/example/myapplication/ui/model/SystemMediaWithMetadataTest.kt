package com.example.myapplication.ui.model

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SystemMediaWithMetadataTest {
    @Test
    fun favoriteAndTagFiltersUseIntersection() {
        assertTrue(
            matchesSystemMediaMetadata(
                starred = true,
                tagIds = listOf(3L),
                starredOnly = true,
                selectedTagId = 3L
            )
        )
        assertFalse(
            matchesSystemMediaMetadata(
                starred = true,
                tagIds = emptyList(),
                starredOnly = true,
                selectedTagId = 3L
            )
        )
        assertFalse(
            matchesSystemMediaMetadata(
                starred = false,
                tagIds = listOf(3L),
                starredOnly = true,
                selectedTagId = 3L
            )
        )
    }

    @Test
    fun selectionUpdateIsIdempotent() {
        var selected = emptySet<String>()
        selected = updateSystemMediaSelection(selected, "image:2", true)
        selected = updateSystemMediaSelection(selected, "image:2", true)
        selected = updateSystemMediaSelection(selected, "image:1", true)
        assertEquals(setOf("image:1", "image:2"), selected)

        selected = updateSystemMediaSelection(selected, "image:1", false)
        assertEquals(setOf("image:2"), selected)
    }
}
