package com.example.myapplication.navigation

import android.net.Uri
import com.example.myapplication.data.database.entities.Media
import com.example.myapplication.data.model.SystemMedia

/**
 * 应用导航路由定义
 */
object Routes {
    // 主要页面
    const val HOME = "home"
    const val COLLECTION_LIST = "collections"
    const val PERSON_LIST = "people"
    const val MEDIA_LIST = "media"
    const val GROUP_LIST = "groups"
    const val SYSTEM_GALLERY = "system_gallery"
    const val SYSTEM_FOLDER_VIEW = "system_folder_view"

    // 系统媒体相关
    const val SYSTEM_MEDIA_DETAIL = "system_media_detail?uri={uri}"
    const val SYSTEM_MEDIA_EDIT = "system_media_edit/{mediaId}"
    const val FOLDER_DETAIL = "folder_detail/{folderName}"
    const val SYSTEM_MEDIA_PICKER = "system_media_picker/{groupId}"

    // 合集相关
    const val COLLECTION_DETAIL = "collection/{collectionId}"
    const val COLLECTION_EDIT = "collection/edit?collectionId={collectionId}"
    const val COLLECTION_ADD = "collection/add"

    // 媒体相关
    const val MEDIA_DETAIL = "media/{mediaId}"
    const val MEDIA_FULLSCREEN =
        "media/fullscreen/{mediaId}?mediaIdListJson={mediaIdListJson}&messageId={messageId}&filterTagId={filterTagId}&filterCollectionId={filterCollectionId}&filterQuery={filterQuery}"
    const val MEDIA_EDIT = "media/edit?mediaId={mediaId}"

    // 标签相关
    const val TAG_LIST = "tags"
    const val TAG_ADD = "tag/add"
    const val TAG_EDIT = "tag/edit?tagId={tagId}"


    // 设置
    const val SETTINGS = "settings"

    // 消息相关
    const val MESSAGE_LIST = "messages?tagId={tagId}"
    const val MESSAGE_LIST_BY_COLLECTION = "messages_by_collection?collectionId={collectionId}"
    const val MESSAGE_DETAIL = "message/{messageId}"
    const val MESSAGE_EDIT = "message/edit?messageId={messageId}"
    const val MESSAGE_ADD = "message/add"

    /**
     * 构建消息列表路由（可选标签过滤）
     */
    fun messageList(tagId: Long? = null): String {
        return if (tagId != null) "messages?tagId=$tagId" else "messages?tagId=-1"
    }

    /**
     * 构建按合集过滤的消息列表路由
     */
    fun messageListByCollection(collectionId: Long) = "messages_by_collection?collectionId=$collectionId"

    /**
     * 构建带参数的合集详情路由
     */
    fun collectionDetail(collectionId: Long) = "collection/$collectionId"

    /**
     * 构建带参数的合集编辑路由
     */
    fun collectionEdit(collectionId: Long) = "collection/edit?collectionId=$collectionId"

    /**
     * 构建带参数的媒体详情路由
     */
    fun mediaDetail(mediaId: Long) = "media/$mediaId"

    /**
     * 构建带参数的全屏媒体详情路由
     */
    fun mediaFullscreen(mediaId: Long) = "media/fullscreen/$mediaId"

    /**
     * 构建带参数的媒体编辑路由
     */
    fun mediaEdit(mediaId: Long) = "media/edit?mediaId=$mediaId"

    /**
     * 构建带参数的标签编辑路由
     */
    fun tagEdit(tagId: Long) = "tag/edit?tagId=$tagId"


    /**
     * 构建带参数的系统媒体详情路由
     */
    fun systemMediaDetail(media: SystemMedia) =
        "system_media_detail?uri=${Uri.encode(media.uri.toString())}"

    /**
     * 构建带参数的系统媒体编辑路由
     */
    fun systemMediaEdit(mediaId: Long) = "system_media_edit/$mediaId"

    /**
     * 构建带参数的文件夹详情路由
     */
    fun folderDetail(folderName: String) =
        "folder_detail/${java.net.URLEncoder.encode(folderName, "UTF-8")}"


    /**
     * 系统文件夹视图路由
     */
    fun systemFolderView() = "system_folder_view"

    /**
     * 构建带参数的消息详情路由
     */
    fun messageDetail(messageId: Long) = "message/$messageId"

    /**
     * 构建带参数的消息编辑路由
     */
    fun messageEdit(messageId: Long) = "message/edit?messageId=$messageId"
}

/**
 * NavController扩展函数
 */
fun androidx.navigation.NavController.navigateToMediaFullscreen(
    mediaId: Long,
    mediaList: List<Media>,
    messageId: Long = -1L,
    filterTagId: Long? = null,
    filterCollectionId: Long? = null,
    filterQuery: String = ""
) {
    // 只传递 ID 列表，避免序列化整个 Media 对象导致 URL 过长
    val mediaIdList = mediaList.map { it.id }
    val mediaIdListJson = java.net.URLEncoder.encode(
        com.google.gson.Gson().toJson(mediaIdList),
        "UTF-8"
    )
    val tagArg = filterTagId ?: -1L
    val collectionArg = filterCollectionId ?: -1L
    val queryArg = java.net.URLEncoder.encode(filterQuery, "UTF-8")
    navigate(
        "media/fullscreen/$mediaId" +
                "?mediaIdListJson=$mediaIdListJson" +
                "&messageId=$messageId" +
                "&filterTagId=$tagArg" +
                "&filterCollectionId=$collectionArg" +
                "&filterQuery=$queryArg"
    )
}

fun androidx.navigation.NavController.navigateToMediaFullscreen(mediaId: Long) {
    navigate("media/fullscreen/$mediaId")
}

/**
 * 底部导航目的地
 */
enum class BottomNavDestination(val route: String) {
    HOME(Routes.HOME),
    COLLECTIONS(Routes.COLLECTION_LIST),
    PEOPLE(Routes.PERSON_LIST),
    MEDIA(Routes.MEDIA_LIST),
    MESSAGES(Routes.MESSAGE_LIST),
    SYSTEM_GALLERY(Routes.SYSTEM_GALLERY),
    TAGS(Routes.TAG_LIST)
}
