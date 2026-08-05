## 1. 系统媒体数据与身份

- [x] 1.1 为 `SystemMedia` 提供由媒体类型与 MediaStore ID（或完整 URI）组成的稳定 key，确保图片和视频同 ID 时不冲突
- [x] 1.2 调整 `SystemMediaRepository`，允许按图片/视频授权状态分别查询 collection，合并后按 `dateModified` 倒序并提供稳定次级排序
- [x] 1.3 实现基于复合身份或 URI 的单项查询/详情定位，替换仅按数字 ID 的未完成逻辑
- [x] 1.4 为 repository 的合并排序、同 ID 不冲突和单类型查询添加单元测试

## 2. Media 页状态与权限

- [x] 2.1 将 `MediaViewModel` 的列表数据源从 Room `MediaRepository` 切换到 `SystemMediaRepository`，移除该页面的 Room 过滤依赖
- [x] 2.2 建模加载中、已加载、无权限和查询失败状态，并提供重试入口
- [x] 2.3 在 `MediaListScreen` 中实现 Android 13+ 图片/视频分类型权限及 Android 12- 读取权限请求，支持仅授权一种类型和 Android 14 部分媒体访问
- [x] 2.4 获得权限后立即加载，并在页面随应用回到前台时刷新；拒绝后不自动重复请求

## 3. 系统媒体网格

- [x] 3.1 保留 `MediaListScreen` 的三列网格、顶部样式和滚动控制底部导航行为，列表元素改为 `SystemMedia`
- [x] 3.2 复用 `SystemMediaCard` 的 `content://` 缩略图、视频标识和时长展示，并使用稳定复合 key
- [x] 3.3 移除或隐藏依赖 Room 星标、标签等元数据的搜索/筛选控件，不创建虚假映射
- [x] 3.4 分别实现加载、空媒体库、无权限和加载失败 UI；无权限和失败状态提供对应操作

## 4. 只读预览导航

- [x] 4.1 调整系统媒体详情路由，使其传递复合身份或编码后的 content URI，而不是仅传数字 ID
- [x] 4.2 将 Media 页项目点击接到 `SystemMediaDetailScreen`，确保图片与视频同 ID 时均打开正确项目
- [x] 4.3 补足系统媒体详情中的只读视频播放，并确保媒体页入口不暴露编辑、删除、移动或上传操作

## 5. 验证

- [x] 5.1 运行 Android 单元测试并执行 `./gradlew assembleDebug`
- [ ] 5.2 在 Android 12 或以下验证传统存储读取权限、混合网格和预览（当前 `minSdk=33`，不适用）
- [ ] 5.3 在 Android 13+ 分别验证全部授权、仅图片、仅视频和拒绝授权
- [ ] 5.4 在 Android 14+ 验证部分照片/视频授权只显示可访问内容
- [ ] 5.5 验证从相机或系统相册返回后列表刷新，且浏览过程不写 Room、不上传、不调用 backend
