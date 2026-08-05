## Context

底部导航的 `MediaListScreen` 当前由 `MediaViewModel` 读取 Room `media` 表，并使用面向后端 `Media` 实体的卡片和全屏预览。与此同时，应用已有独立的系统相册实现：`SystemMediaRepository` 查询 MediaStore 图片与视频，`SystemGalleryViewModel` 处理加载/过滤，`SystemMediaCard` 能直接加载 `content://` 缩略图，相关运行时权限也已在多个系统媒体页面中处理。

第一阶段只改变“媒体”页的浏览数据源。设备 MediaStore 是该页面的真相源；Room 和 backend 媒体仍服务于消息及同步，但不参与此页面的列表生成。

## Goals / Non-Goals

**Goals:**
- 底部导航“媒体”页显示应用有权访问的全部系统图片和视频。
- 保持现有三列网格、顶部视觉结构、加载/空状态及底部栏滚动体验。
- 正确处理 Android 13+ 分类型媒体权限、Android 14 部分照片访问和旧版本读取权限。
- 使用 `content://` URI 加载缩略图，并支持图片与视频的只读预览。
- 避免图片表与视频表数字 ID 重叠造成 Compose key 或详情定位冲突。

**Non-Goals:**
- 上传、备份或同步系统媒体。
- 将系统媒体复制到私有目录或插入 Room。
- 删除、回收站、编辑、移动、重命名、收藏、标签和评分。
- 相册/文件夹浏览、搜索和高级筛选。
- 引入 Room schema 迁移或 backend API 变更。

## Decisions

### 1. MediaStore 是媒体页的唯一列表数据源

`MediaViewModel` 改为通过 `SystemMediaRepository` 加载 `SystemMedia`，不再调用 `MediaRepository.getAllMedia()`。现有独立 `SystemGalleryViewModel` 的查询和权限状态模式可复用或收敛到 `MediaViewModel`，但底部导航继续使用 `MediaListScreen` 和 `Routes.MEDIA_LIST`，避免新增平行入口。

**替代方案：** 直接把 `Routes.MEDIA_LIST` 指向 `SystemGalleryScreen`。该方式改动较少，但会丢失现有 Media 页样式及页面状态职责，并保留两套重叠页面，因此不采用。

### 2. 使用媒体类型 + ID（或 URI）作为稳定身份

MediaStore 的图片和视频来自不同 collection，数字 `_ID` 可能相同。列表 key 和详情参数必须包含媒体类型，例如 `image:123` / `video:123`，或直接使用完整 URI；不得仅使用 `id: Long`。

详情页优先传递编码后的 URI/复合 key，或由 repository 按类型和 ID 查询。该阶段不依赖文件系统真实路径。

### 3. 权限按“已授权可见内容”处理

- Android 13+ 分别检查/请求 `READ_MEDIA_IMAGES` 与 `READ_MEDIA_VIDEO`。
- Android 14 兼容“选择部分照片和视频”；只展示系统返回为可访问的项目。
- Android 12 及以下使用 `READ_EXTERNAL_STORAGE`。
- 图片或视频仅有一类权限时，页面仍加载已授权类型，不把部分授权视为整体失败。
- 权限完全未授予时显示说明和授权入口；拒绝后不循环弹窗。

### 4. 保留页面外观，替换 tile 与不可用操作

继续使用 `LazyVerticalGrid(GridCells.Fixed(3))`、顶部区域和底栏显隐逻辑。网格项改用 `SystemMediaCard` 或其缩略图能力，以 Coil/ContentResolver 读取 URI。由于 `SystemMedia` 尚无 Room 星标和标签，移除或隐藏当前依赖这些字段的筛选控件；第一阶段不伪造对应状态。

视频 tile 保留播放标识和时长。加载、无权限、空媒体库、查询失败分别呈现明确状态。

### 5. 只读预览沿用系统媒体详情链路

媒体点击进入 `SystemMediaDetailScreen`（必要时调整其参数为复合身份/URI），而不是把 `SystemMedia` 临时转换成 Room `Media` 后进入现有 `MediaViewerScreen`。这样可避免假 ID、文件路径依赖和意外持久化。

第一阶段预览只要求可查看图片和播放视频；任何编辑入口均不从媒体页暴露。

### 6. 首次进入与回到前台时刷新

首次获得权限后加载媒体。页面回到前台时重新查询，以反映用户在系统相册或相机中的变化。第一阶段不引入 `ContentObserver` 或 Paging；保留现有一次性 MediaStore 查询，以控制范围。后续若大图库性能不足，再单独引入分页和增量监听。

## Risks / Trade-offs

- **大图库一次性加载成本**：当前 repository 会查询并合并全部图片和视频。第一阶段接受这一点，构建和设备验证时关注内存与首屏时间；分页另立变更。
- **Android 14 权限差异**：部分授权行为依赖系统版本。实现必须按实际授权分别加载图片和视频，并在恢复时刷新。
- **详情定位冲突**：旧详情路由仅传数字 ID 会错误定位。通过复合身份或 URI 消除冲突。
- **重复系统相册代码**：已有 `SystemGalleryScreen` 与新媒体页职责重叠。优先复用 repository、状态与 tile，不复制查询代码；是否删除旧入口不属于本阶段。
- **视频预览现状不完整**：现有系统详情视频播放存在待办。若验证发现仍是占位，本变更需要补足只读播放，但不扩展编辑能力。

## Migration Plan

1. 调整系统媒体身份和 repository 查询接口。
2. 将 Media 页 ViewModel 数据源切换到 MediaStore，并加入分类型权限状态。
3. 替换网格 tile 和页面状态，移除 Room 专属筛选操作。
4. 接通复合身份的系统媒体只读详情导航。
5. 构建并在不同 Android 权限场景下验证。

无需数据库迁移；回滚时恢复 `MediaViewModel` 的 Room 数据源和原详情导航即可。

## Open Questions

- 暂无阻塞项。搜索、文件夹视图、分页和 ContentObserver 均明确留待后续变更。
