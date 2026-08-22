## Context

Media 页面当前展示 `SystemMediaWithMetadata`，数据来自 MediaStore 与本机 metadata 覆盖层。Message 发送管线接收 `MediaFileInfo`，预处理时复制到 `files/media`、计算 hash、生成缩略图，再创建 Room `Message`/`Media`/`MessageMedia` 并上传。失败重试只接受真实文件路径。

本变更要求在 Media 网格直接多选并建立一条 Message，同时不复制系统文件。因此 Room `Media` 必须能够表达 MediaStore 引用，所有媒体读取点需要从“只接受文件路径”升级为“按来源打开内容”。backend 仍需要接收文件字节，以便其他设备和系统媒体删除后的已同步 Message 可用。

## Goals / Non-Goals

**Goals:**
- 长按进入多选，支持拖动经过项目的连续选择。
- 多个系统媒体按当前网格顺序组成一条 Message。
- 本机始终直接引用 MediaStore，不创建应用私有媒体或缩略图副本。
- 首次上传和失败重试均可直接读取 `content://` URI。
- 已同步媒体在系统文件不可访问时回退远端资源。

**Non-Goals:**
- 不新增 Message 文本、标签或 collection 的编辑步骤；本次“创建”直接创建纯媒体 Message。
- 不把系统媒体本机收藏或标签复制给 Room `Media`/Message。
- 不修改、删除或移动 MediaStore 文件。
- 不修改 backend API 或改变服务器媒体持久化行为。
- 不支持跨筛选结果保留隐藏项目的选择。

## Decisions

### 1. `Media` 使用显式来源和 content URI

Room `Media` 增加：

- `sourceType`: `REMOTE`、`APP_FILE`、`MEDIA_STORE`。
- `contentUri`: 仅 `MEDIA_STORE` 使用的 `content://` 字符串。
- `originalFileName`: multipart 上传文件名。

`localMediaPath` 继续只表示真实文件路径，不承载 `content://`。`filePath`/`thumbnailPath` 等展示解析改为优先可访问的本地来源，再回退远端 URL。现有同步下发媒体默认归为 `REMOTE`；下载或应用私有文件归为 `APP_FILE`。

选择系统媒体时直接利用 `SystemMedia` 已有 MIME、大小、宽高、时长和 URI 构造 `Media`。仍通过 URI 流计算与 backend 一致的 Blake2b，用 `fileHash` 复用已有 Room `Media`，避免同一内容产生重复媒体行。

### 2. 不复制、不生成私有缩略图

MediaStore 来源的 `localMediaPath` 和 `localThumbnailPath` 保持 null。网格和 Message UI 使用 `contentUri` 交给 Coil/Media3/ContentResolver；系统缩略图仍由 MediaStore 提供。服务器上传只读取 URI 字节，不改变或复制源文件。

### 3. 统一媒体内容读取抽象

发送和重试共享一个按 `Media` 来源构建 multipart body 的组件：

- `APP_FILE`: 读取 `File(localMediaPath)`。
- `MEDIA_STORE`: 通过 `ContentResolver.openInputStream(Uri.parse(contentUri))` 流式读取，并使用已知 `fileSize` 提供 content length。
- 已有 `remoteMediaUrl` 且无需重新上传时，沿用当前服务器路径/同步策略；若当前 create-from-client 流程仍要求文件路径，则只上传可访问本地来源。

URI request body 每次写入时重新打开 InputStream，避免持有游标或流。读取异常向发送管线返回失败，不生成空文件。

### 4. Message 创建由 MessageViewModel 负责

`MediaViewModel` 只管理网格选择；确认后把有序 `List<SystemMedia>` 交给现有 `MessageViewModel` 的系统媒体发送入口。该入口：

1. 在 IO dispatcher 计算 hash，并构造 MEDIA_STORE `Media`，不复制文件。
2. 单事务创建一条 `Message(sendStatus=PUSHING)`、全部 Media 和 junction。
3. Message 立即进入 Paging。
4. 并发从 content URI 上传文件。
5. 调用现有 `POST /messages/create-from-client`，成功后应用远端 URL。
6. 网络错误标记 `PENDING_SYNC`，来源不可访问等业务错误标记 `PUSH_FAILED`。

创建开始后退出选择模式并清空选择；发送状态由 Message 页面现有机制反馈，Media 页面不维持上传进度。

### 5. 选择状态使用 stableKey，并保持可见顺序

选择集合使用 `SystemMedia.stableKey`，避免图片和视频 ID 冲突。创建时从当前筛选后的 `mediaList` 过滤选中项，因此 MessageMedia position 与网格顺序一致，而不是手势经过顺序。

筛选条件在选择模式中保持可用但一旦改变，已不再可见的 key 从选择集合移除，避免创建用户看不到的项目。刷新后不存在的媒体同样移除。

### 6. 长按与滑动选择语义

普通模式：
- 点击打开预览。
- 长按进入选择模式并选中起始项。

选择模式：
- 点击项目切换选中状态。
- 拖动手势开始时根据触点下的起始项目决定本次手势动作：起始项未选中则本次为“添加”，已选中则本次为“移除”。
- 手指跨越项目时，对每个 stableKey 最多执行一次相同动作，避免一个项目内多次 pointer move 导致反复切换。
- 拖动到网格上下边缘时允许 LazyGrid 正常滚动；项目命中基于 `LazyGridLayoutInfo.visibleItemsInfo` 和当前 viewport 坐标。
- 选择数量变为零时仍保持选择模式，直到用户点击取消或重新选择，避免浮动栏突然消失。

手势检测放在网格层，以便跨项目命中；卡片只负责长按/点击和选中视觉状态。

### 7. 底部浮动操作栏

选择模式时在网格上方叠加底部居中的浮动 Surface，显示“已选择 N 项”、“取消”和“创建”。

- `创建` 仅在 N > 0 且未提交时启用。
- `取消` 清空集合并退出选择模式。
- 提交期间禁用重复创建。
- 操作栏与底部导航保持安全间距；进入选择模式时保持底部导航可见性策略稳定，不让滚动自动隐藏操作栏。

### 8. 生命周期和失效处理

MediaStore URI 是本机引用，不能保证永久存在。应用不依赖 `takePersistableUriPermission`，因为常规 MediaStore URI 在已授予媒体读取权限时可重新访问。

- 已同步：content URI 读取失败时展示远端 URL/缩略图。
- 未同步：保留 Message 和 Media，标记 `PUSH_FAILED`；用户恢复权限或文件后可重试。
- 文件永久删除且无远端 URL：显示“原始媒体不可用”，不静默删除 Message。

## Risks / Trade-offs

- 直接引用节省空间，但用户删除系统文件会使未同步消息不可恢复。
- hash 计算需要读取媒体；大文件沿用首尾采样策略，但仍有 IO 成本。
- Compose 跨网格滑动选择与滚动存在手势竞争，需要真机验证不同屏幕密度和快速滑动。
- Room 当前使用 destructive migration，版本提升会清空本地数据；符合项目现有策略但必须明确验证。
- 同一 hash 已存在 APP_FILE/REMOTE Media 时会复用该行；实现必须避免用 MEDIA_STORE 字段覆盖更可靠的现有本地路径，只补充缺失来源信息或直接复用。

## Migration Plan

1. 扩展 `Media` schema，提升 Room 版本并更新同步映射默认来源。
2. 增加基于 File/content URI 的统一媒体读取和 multipart request body。
3. 增加不复制的系统媒体 Message 创建入口及重试支持。
4. 更新缩略图、预览和播放器的本地来源解析及远端回退。
5. 实现 Media 网格选择状态、跨项目滑动手势和底部浮动操作栏。
6. 添加单元/UI 测试并在真机验证权限、删除和快速拖动场景。
