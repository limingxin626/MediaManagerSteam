## ADDED Requirements

### Requirement: 数据目录配置与持久化

Mac app SHALL 在首次启动时引导用户选择 `DATA_ROOT` 目录,并将该目录的绝对路径持久化到 `UserDefaults` 的 `dataRoot` key。再次启动 MUST 自动读取已保存的路径,无需用户重复选择。

#### Scenario: 首次启动未配置 DATA_ROOT

- **WHEN** 用户第一次启动 Mac app,`UserDefaults` 中无 `dataRoot` 值
- **THEN** app 显示引导界面,包含"选择数据目录"按钮
- **AND** 点击按钮触发 `NSOpenPanel`,只允许选择目录(`canChooseDirectories=true`, `canChooseFiles=false`)
- **AND** 用户确认选择后,所选路径写入 `UserDefaults.dataRoot`

#### Scenario: 再次启动已配置 DATA_ROOT

- **WHEN** 用户已配置过 `DATA_ROOT`,再次启动 app
- **THEN** app 自动从 `UserDefaults.dataRoot` 读取路径
- **AND** 不显示引导界面,直接进入主界面

#### Scenario: 用户手动重新选择 DATA_ROOT

- **WHEN** 用户在 Settings 界面点击"更换数据目录"
- **THEN** 再次触发 `NSOpenPanel`,选择后覆盖 `UserDefaults.dataRoot`
- **AND** app 重新初始化数据库连接

### Requirement: 数据目录校验

App SHALL 在每次打开数据库连接前校验 `DATA_ROOT` 指向的目录有效。校验失败时 MUST 显示错误提示并提供"重新选择目录"操作,不得静默崩溃或显示空白界面。

#### Scenario: DATA_ROOT 目录不存在

- **WHEN** `UserDefaults.dataRoot` 指向的路径在文件系统上不存在(用户删除了目录或换了机器)
- **THEN** app 显示错误"数据目录不存在: {path}"
- **AND** 提供"重新选择目录"按钮

#### Scenario: DATA_ROOT 中缺少 db.sqlite3

- **WHEN** 目录存在但其中没有 `db.sqlite3` 文件
- **THEN** app 显示错误"未找到数据库文件 db.sqlite3"
- **AND** 提供"重新选择目录"按钮

#### Scenario: 数据库 schema 不匹配

- **WHEN** 数据库文件存在,但执行 `SELECT 1 FROM media LIMIT 1` 抛出错误(表不存在或列缺失)
- **THEN** app 显示错误"数据库格式不兼容: {具体错误}"
- **AND** 提供"重新选择目录"按钮

### Requirement: SQLite 只读连接

App SHALL 通过 GRDB.swift 以**只读模式**(`Configuration.readonly = true`)打开 `DATA_ROOT/db.sqlite3`,禁止任何写入操作。整个 app 生命周期内 MUST 复用单例 `DatabaseQueue`。

#### Scenario: 数据库连接初始化

- **WHEN** app 启动且 `DATA_ROOT` 校验通过
- **THEN** 创建唯一的 `DatabaseQueue` 实例,`Configuration.readonly = true`
- **AND** 实例通过单例(`LocalDatabase.shared`)暴露给数据访问层

#### Scenario: 尝试执行写 SQL

- **WHEN** 任何代码路径试图通过只读连接执行 INSERT/UPDATE/DELETE
- **THEN** SQLite 返回错误(`SQLITE_READONLY`),GRDB 抛出异常
- **AND** 该异常 MUST 不被静默吞掉,至少打到日志

### Requirement: Media 表 GRDB 映射

App SHALL 定义 `MediaRecord` 结构体,字段与 backend `backend/app/models/__init__.py` 的 `Media` 表**一一对齐**。列名使用 snake_case,通过 `databaseColumnDecodingStrategy = .convertFromSnakeCase` 或手动 `CodingKeys` 映射。

#### Scenario: 读取 Media 行

- **WHEN** 执行 `MediaRecord.fetchOne(db, key: 1)`
- **THEN** 返回的 `MediaRecord` 实例包含 `id`/`filePath`/`fileSize`/`mimeType`/`width`/`height`/`durationMs`/`rating`/`starred`/`viewCount`/`createdAt`/`updatedAt`/`videoMediaId`/`frameMs`/`startMs`/`endMs`/`takenAt`/`gpsLat`/`gpsLng`/`orientation`/`cameraMake`/`cameraModel`/`lens`/`videoCodec`/`audioCodec`/`hasAudio`/`fps`/`bitrate` 等所有列

#### Scenario: MediaRecord 转换为 UI Media 模型

- **WHEN** 数据层把 `MediaRecord` 暴露给 ViewModel
- **THEN** 通过转换扩展生成 `Models.swift` 中已定义的 `Media` 结构体
- **AND** UI 层(`MediaLibraryView`)无需感知 GRDB 的存在

### Requirement: Tag 批量加载避免 N+1

当 ViewModel 一次获取 N 条 Media 时,数据访问层 SHALL 用**单条 SQL**(`WHERE media_id IN (?, ?, ...)` join `media_tag` 与 `tag`)批量取出所有标签关联,在内存中 groupBy 分配给各 Media,不得每条 Media 单独发一次查询。

#### Scenario: 网格首屏加载 40 条 Media

- **WHEN** `MediaRepository.list(limit: 40, ...)` 被调用
- **THEN** 数据层先查 40 条 Media,再用 1 条 SQL 批量查 `media_tag` join `tag`(`WHERE media_id IN (...)`)
- **AND** 总查询次数为 2 次(Media + Tag 关联),不随 N 增长

### Requirement: 本地媒体文件路径解析

App SHALL 提供工具函数把 backend 存储的相对路径(`file_path` 列,如 `uploads/2026/06/04/xxx.mp4`)解析为绝对 `URL`,基于当前 `DATA_ROOT`。缩略图路径 MUST 固定按 `DATA_ROOT/data/thumbs/{media.id}.webp` 拼接。

#### Scenario: 解析媒体原文件 URL

- **WHEN** 调用 `Media.localFileURL` 计算属性,`DATA_ROOT = /Volumes/Data/MM` 且 `file_path = uploads/2026/06/04/abc.mp4`
- **THEN** 返回 `file:///Volumes/Data/MM/uploads/2026/06/04/abc.mp4`

#### Scenario: 解析缩略图 URL

- **WHEN** 调用 `Media.localThumbURL`,`DATA_ROOT = /Volumes/Data/MM` 且 `media.id = 1234`
- **THEN** 返回 `file:///Volumes/Data/MM/data/thumbs/1234.webp`

#### Scenario: DATA_ROOT 未配置时调用路径解析

- **WHEN** `UserDefaults.dataRoot` 为 nil 时调用 `localFileURL` 或 `localThumbURL`
- **THEN** 返回 nil(不崩溃),UI 层显示占位图
