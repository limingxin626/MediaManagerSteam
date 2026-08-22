## ADDED Requirements

### Requirement: Enter and exit media selection mode

Android Media 页面 SHALL 允许用户长按系统媒体进入多选模式，并 SHALL 在进入时选中长按项目。

#### Scenario: 长按首个项目
- **WHEN** 用户在普通浏览模式长按一个系统媒体卡片
- **THEN** 页面进入多选模式
- **AND** 该媒体显示为已选中
- **AND** 普通点击打开预览的动作不被触发

#### Scenario: 取消选择
- **WHEN** 用户点击底部浮动操作栏的“取消”
- **THEN** 页面退出多选模式
- **AND** 清空全部选择

### Requirement: Tap and drag selection

多选模式 SHALL 支持点击切换单项选择，并 SHALL 支持通过一次连续拖动对手指经过的可见网格项目执行一致的添加或移除操作。

#### Scenario: 拖动添加项目
- **WHEN** 用户从一个未选中项目开始拖动并经过多个项目
- **THEN** 起始项和经过的每个项目均变为已选中
- **AND** 同一项目在该次拖动中只处理一次

#### Scenario: 拖动移除项目
- **WHEN** 用户从一个已选中项目开始拖动并经过多个项目
- **THEN** 起始项和经过的每个项目均变为未选中
- **AND** 同一项目在该次拖动中只处理一次

#### Scenario: 选择模式点击项目
- **WHEN** 用户在多选模式短按一个项目
- **THEN** 页面切换该项目的选中状态
- **AND** 不打开媒体预览

### Requirement: Floating selection actions

多选模式 SHALL 在页面底部显示浮动操作栏，其中包含选中数量、“创建”和“取消”按钮。

#### Scenario: 没有选中项目
- **WHEN** 用户取消选择全部项目但仍处于多选模式
- **THEN** 浮动操作栏继续显示
- **AND** “创建”按钮不可用

#### Scenario: 防止重复创建
- **WHEN** 用户点击“创建”且创建请求正在提交
- **THEN** “创建”按钮不可再次触发

### Requirement: One message from ordered selection

点击“创建” SHALL 将全部选中系统媒体按当前网格顺序组成一条 Message，并为每个媒体创建对应的 `MessageMedia.position`。

#### Scenario: 创建多媒体 Message
- **WHEN** 用户选择三个媒体并点击“创建”
- **THEN** 本地只创建一条 Message
- **AND** Message 关联三个 Media
- **AND** 关联顺序与当前网格中的显示顺序一致
- **AND** Message 立即以发送中状态出现在消息列表

#### Scenario: 创建成功后清理选择
- **WHEN** 本地 Message 创建已经开始
- **THEN** Media 页面退出多选模式并清空选择
- **AND** 后台继续上传和同步该 Message

### Requirement: MediaStore references are not copied

从 Media 页面创建 Message 时，应用 SHALL 直接引用原始 MediaStore 项，并 SHALL NOT 将原文件或缩略图复制到应用私有目录。

#### Scenario: 构造系统来源 Media
- **WHEN** 一个选中的系统媒体首次写入 Room Media
- **THEN** Media 保存明确的 MEDIA_STORE 来源和 `content://` URI
- **AND** `localMediaPath` 与 `localThumbnailPath` 保持为空
- **AND** Media 保存原始文件名、MIME、大小、宽高和视频时长

#### Scenario: 内容去重
- **WHEN** 系统媒体内容 hash 已对应一个 Room Media
- **THEN** Message 复用现有 Media ID
- **AND** 不创建重复 Media 行

### Requirement: Upload and retry read MediaStore content

首次发送和失败重试 SHALL 能通过 `ContentResolver` 从 MediaStore URI 流式读取内容，并 SHALL 继续使用现有 backend 上传与 `create-from-client` 协议。

#### Scenario: 首次上传系统媒体
- **WHEN** 本地 Message 创建完成且系统 URI 可访问
- **THEN** 上传请求直接读取 content URI 的字节
- **AND** 上传使用原始文件名和 MIME 类型
- **AND** 不创建中间文件

#### Scenario: 网络失败后重试
- **WHEN** 上传因网络问题进入待同步状态且用户重试
- **THEN** 重试重新打开保存的 content URI
- **AND** 成功后应用 backend 返回的远端 URL

#### Scenario: 源媒体不可访问
- **WHEN** 系统媒体已删除或读取权限失效且没有可上传的本地来源
- **THEN** Message 保持在本地并标记推送失败
- **AND** 不上传空文件或创建不完整的 backend Message

### Requirement: Local source with remote fallback

媒体展示 SHALL 优先使用可访问的 MediaStore URI，并在其不可访问且已有远端 URL 时回退远端资源。

#### Scenario: 已同步系统文件被删除
- **WHEN** 一个已同步 Media 的 content URI 不再可读取
- **THEN** 缩略图和预览使用对应远端 URL
- **AND** Message 关联保持不变

#### Scenario: 无可用来源
- **WHEN** content URI 不可读取且没有远端 URL
- **THEN** UI 显示原始媒体不可用状态
- **AND** 不静默删除 Message 或 Media

### Requirement: System metadata remains independent

创建 Message SHALL NOT 自动继承系统媒体覆盖层中的收藏或标签，也 SHALL NOT 改变该覆盖层。

#### Scenario: 从已收藏且有标签的系统媒体创建
- **WHEN** 用户选择一个带本机收藏和标签的系统媒体创建 Message
- **THEN** 新 Message 不自动获得这些标签
- **AND** 新 Room Media 不自动变为收藏
- **AND** 原 system media metadata 保持不变
