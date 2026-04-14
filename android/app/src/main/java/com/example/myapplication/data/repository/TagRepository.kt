package com.example.myapplication.data.repository

import com.example.myapplication.data.database.dao.TagDao
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.database.entities.MediaTag
import com.example.myapplication.data.database.entities.Tag
import kotlinx.coroutines.flow.Flow

/**
 * 标签仓库
 * 简化版本，只包含基础功能
 */
class TagRepository(private val tagDao: TagDao) {

    /**
     * 获取所有标签
     */
    fun getAllTags(): Flow<List<Tag>> = tagDao.getAllTags()

    /**
     * 根据ID获取标签
     */
    suspend fun getTagById(tagId: Long): Tag? = tagDao.getTagById(tagId)

    /**
     * 根据名称获取标签
     */
    suspend fun getTagByName(name: String): Tag? = tagDao.getTagByName(name)

    /**
     * 创建或获取标签
     */
    suspend fun createOrGetTag(name: String, category: String? = null): Tag {
        val existingTag = tagDao.getTagByName(name)
        return if (existingTag != null) {
            existingTag
        } else {
            val newTag = Tag(name = name.trim(), category = category, color = randomTagColor())
            val id = tagDao.insertTag(newTag)
            newTag.copy(id = id)
        }
    }

    companion object {
        private val TAG_COLORS = listOf(
            "#E53935", "#D81B60", "#8E24AA", "#5E35B1",
            "#3949AB", "#1E88E5", "#039BE5", "#00ACC1",
            "#00897B", "#43A047", "#7CB342", "#C0CA33",
            "#FDD835", "#FFB300", "#FB8C00", "#F4511E",
            "#6D4C41", "#546E7A"
        )

        private fun randomTagColor(): String = TAG_COLORS.random()
    }

    /**
     * 更新标签
     */
    suspend fun updateTag(tag: Tag) = tagDao.updateTag(tag)

    /**
     * 删除标签
     */
    suspend fun deleteTag(tag: Tag) = tagDao.deleteTag(tag)

    /**
     * 获取媒体的标签
     */
    fun getTagsForMedia(mediaId: Long): Flow<List<Tag>> = tagDao.getTagsForMedia(mediaId)

    /**
     * 为媒体设置标签
     */
    suspend fun setTagsForMedia(mediaId: Long, tags: List<Tag>) {
        // 删除现有标签关联
        tagDao.deleteAllTagsForMedia(mediaId)

        // 添加新的标签关联
        if (tags.isNotEmpty()) {
            val mediaTags = tags.map { tag ->
                MediaTag(mediaId = mediaId, tagId = tag.id)
            }
            tagDao.insertMediaTags(mediaTags)
        }
    }

    /**
     * 为媒体添加标签
     */
    suspend fun addTagToMedia(mediaId: Long, tagId: Long) {
        val mediaTag = MediaTag(mediaId = mediaId, tagId = tagId)
        tagDao.insertMediaTag(mediaTag)
    }

    /**
     * 从媒体移除标签
     */
    suspend fun removeTagFromMedia(mediaId: Long, tagId: Long) {
        val mediaTag = MediaTag(mediaId = mediaId, tagId = tagId)
        tagDao.deleteMediaTag(mediaTag)
    }

    /**
     * 获取标签关联的所有媒体
     */
    fun getMediaForTag(tagId: Long): Flow<List<Media>> = tagDao.getMediaForTag(tagId)

    /**
     * 获取标签关联的消息数量
     */
    suspend fun getMessageCountForTag(tagId: Long): Int = tagDao.getMessageCountForTag(tagId)

    /**
     * 搜索标签
     */
    fun searchTags(query: String): Flow<List<Tag>> = tagDao.searchTags(query)

    /**
     * 从字符串创建标签（兼容旧数据）
     */
    suspend fun createTagsFromString(tagString: String): List<Tag> {
        if (tagString.isBlank()) return emptyList()

        val tagNames = tagString.split(",")
            .map { it.trim() }
            .filter { it.isNotBlank() }
            .distinct()

        return tagNames.map { name ->
            createOrGetTag(name)
        }
    }

    /**
     * 从字符串为媒体设置标签
     */
    suspend fun setTagsForMediaFromString(mediaId: Long, tagString: String?) {
        if (tagString.isNullOrBlank()) {
            tagDao.deleteAllTagsForMedia(mediaId)
            return
        }

        val tags = createTagsFromString(tagString)
        setTagsForMedia(mediaId, tags)
    }
}