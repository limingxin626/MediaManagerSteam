## Why

Android 当前底部导航的“媒体”页面读取 Room 中已经导入或同步的媒体，用户必须先上传或保存记录后才能看到内容。这与“直接管理手机媒体、像系统相册一样浏览”的目标不符。项目已经具备 MediaStore 查询、权限请求和系统媒体缩略图组件，可以先让现有媒体页直接展示设备上所有已授权的图片和视频，为后续管理与按需同步建立入口。

## What Changes

- 将 Android 底部导航“媒体”页面的数据源从 Room `Media` 切换为设备 `MediaStore`。
- 展示应用当前有权访问的全部图片和视频，并按最近修改时间倒序排列。
- 在媒体页内处理 Android 版本对应的图片/视频读取权限，以及 Android 14 部分照片授权。
- 复用现有媒体页的三列网格、顶部样式和底部栏滚动行为，并使用已有系统媒体缩略图组件渲染 `content://` URI。
- 点击项目进入只读的系统媒体预览；使用图片/视频复合身份，避免不同 MediaStore 集合的数字 ID 冲突。
- 暂不上传媒体、不复制到应用目录、不写入 Room，也不提供删除、编辑、移动、收藏或标签操作。

## Capabilities

### New Capabilities
- `system-media-gallery`: Android 媒体页读取并展示 MediaStore 中应用可访问的图片和视频，包含权限、加载状态、排序、网格和只读预览行为。

### Modified Capabilities

（无已有 spec 需要修改）

## Impact

- `android/.../ui/screens/media/MediaListScreen.kt`：改为消费系统媒体状态并渲染 MediaStore 内容。
- `android/.../ui/viewmodel/MediaViewModel.kt`：不再为该页面查询 Room，改为协调权限和 `SystemMediaRepository`。
- `android/.../data/repository/SystemMediaRepository.kt`：作为媒体页数据源，并补足稳定复合身份/单项查询所需能力。
- `android/.../ui/components/SystemMediaCard.kt`：复用系统媒体缩略图与视频标识。
- `android/.../MainActivity.kt`、`navigation/Navigation.kt`：媒体页点击导航到只读系统媒体预览。
- Android manifest 已声明相关读取权限；本变更不影响 backend、Vue、Mac、Room schema 或同步协议。
