## 1. 接入 GRDB 与 DATA_ROOT 配置

- [ ] 1.1 Xcode 工程通过 SPM 添加依赖 `https://github.com/groue/GRDB.swift`(版本 v6.x),link 到 `MyNote` target  **【MAC_TODO §1.1】**
- [ ] 1.2 确认 / 调整 `MyNote.xcodeproj` 的 macOS deployment target ≥ 14.0(为 `NSImage` 原生 webp 解码),在 `design.md` Open Question 1 记录最终选择  **【MAC_TODO §1.2】**
- [x] 1.3 新建 `MyNote/MyNote/Settings.swift`:暴露 `dataRoot: URL?` 计算属性,读写 `UserDefaults.standard` 的 `dataRoot` key(String 路径 ↔ URL)
- [x] 1.4 新建 `MyNote/MyNote/DataRootPicker.swift`:封装 `NSOpenPanel`(`canChooseDirectories=true`, `canChooseFiles=false`, `allowsMultipleSelection=false`)的同步选择函数
- [x] 1.5 新建 `MyNote/MyNote/LocalDatabase.swift`:`final class LocalDatabase`,单例 `shared`,持有 `DatabaseQueue?`,提供 `open(rootURL: URL) throws` 与 `close()` 方法,`Configuration.readonly = true`
- [x] 1.6 实现 DATA_ROOT 校验逻辑:`LocalDatabase.validate(rootURL:)` 检查目录存在 + `db.sqlite3` 存在 + `SELECT 1 FROM media LIMIT 1` 成功,失败抛带描述的 `DataRootError`
- [x] 1.7 改造 `MyNoteApp.swift`:启动时若 `Settings.dataRoot == nil` 显示 onboarding 引导界面;若有值则调 `LocalDatabase.shared.open(...)`;失败显示错误界面 + 重选按钮
- [x] 1.8 在 Settings 界面(可暂时简陋,如 menu bar 项或 ContentView 角落按钮)加 "更换数据目录" 入口,触发重新选择并 reopen 数据库 — 已加在 ContentView 工具栏
- [x] 1.9 启动后控制台打印 `SELECT COUNT(*) FROM media`,验证连接成功 — 已在 `MyNoteApp.tryOpen()` 实现

## 2. Media 表 GRDB 映射

- [x] 2.1 新建 `MyNote/MyNote/MediaRecord.swift`:`struct MediaRecord: Codable, FetchableRecord, TableRecord`,`databaseTableName = "media"`,字段与 `backend/app/models/__init__.py:82` 的 `Media` 表所有列一一对齐(snake_case 列名通过 `CodingKeys` 显式映射或 `databaseDecodingUserInfo` 策略转换)
- [x] 2.2 在 `MediaRecord.swift` 加扩展 `func toUIModel(tags: [MessageTag]) -> Media`,把 GRDB record 转成现有 `Models.swift` 的 `Media` 结构体(暂传空 tags 数组,2.x 后填充)
- [x] 2.3 在 `Models.swift` 的 `Media` 加计算属性 `localThumbURL: URL?` 与 `localFileURL: URL?`,基于 `Settings.dataRoot` 拼接路径(dataRoot 为 nil 时返回 nil)
- [ ] 2.4 单元测试或 Playground 验证:`MediaRecord.fetchAll(db)` 可取出 Media 行,关键字段 (`id`/`file_path`/`mime_type`/`starred`/`created_at`) 都正确解码  **【MAC_TODO §2.1 启动后 console 打印即验证】**

## 3. MediaRepository 与分页

- [x] 3.1 新建 `MyNote/MyNote/MediaRepository.swift`:`final class MediaRepository`,持有 `DatabaseQueue` 引用
- [x] 3.2 实现 `func list(cursor: String?, limit: Int, type: String?, starredOnly: Bool) async throws -> ([MediaRecord], hasMore: Bool, nextCursor: String?)`,SQL 使用 `WHERE (created_at, id) < (?, ?)` 复合游标 + `ORDER BY created_at DESC, id DESC LIMIT N+1` 模式;取 limit+1 行判定 has_more
- [x] 3.3 处理 cursor 解析:`"{iso}|{int}"` split,格式错误抛 `RepositoryError.invalidCursor`
- [x] 3.4 加 type 过滤:`type == "image"` → `AND mime_type LIKE 'image/%'`;`type == "video"` → `AND mime_type LIKE 'video/%'`
- [x] 3.5 加 starredOnly 过滤:true → `AND starred = 1`
- [x] 3.6 实现 `func tagsForMedia(ids: [Int]) async throws -> [Int: [MessageTag]]`:单条 SQL join `media_tag` + `tag` `WHERE media_id IN (...)`,内存 groupBy — 作为 `MediaRepository.fetchTags` 私有静态方法实现
- [x] 3.7 `list()` 内部串起来:先查 MediaRecord,再批量查 tags,组装最终 `[Media]` 返回

## 4. MediaSource 协议与 LocalMediaSource

- [x] 4.1 新建 `MyNote/MyNote/MediaSource.swift`:`protocol MediaSource` 含 `func list(cursor:limit:type:starredOnly:) async throws -> MediaCursorResponse`
- [x] 4.2 实现 `final class LocalMediaSource: MediaSource`,包装 `MediaRepository`,返回 `MediaCursorResponse`(复用 `Models.swift` 中已定义的类型)
- [x] 4.3 实现 `final class APIMediaSource: MediaSource`,内部转调现有 `APIClient.getMedia(...)`(签名对齐,starredOnly bool → Optional Bool)—— 用于回退验证
- [x] 4.4 改造 `MediaLibraryViewModel.swift`:构造函数从 `init(apiClient: APIClient = APIClient())` 改为 `init(mediaSource: MediaSource = LocalMediaSource())`,内部 `apiClient.xxx` 全部改为 `mediaSource.list(...)`
- [x] 4.5 删除 `MediaLibraryViewModel.toggleMediaStarred` 方法(写操作,第一期不做),并搜索 `MediaLibraryView` 内对应按钮入口隐藏 — 网格 cell 的 starred 按钮改成只读显示;Detail 视图已重写不含 toggle

## 5. 本地缩略图加载

- [x] 5.1 新建 `MyNote/MyNote/LocalImageLoader.swift`:`final class LocalImageLoader`,单例 `shared`,持有 `NSCache<NSNumber, NSImage>`(`countLimit = 500`,`totalCostLimit` 视情况) — 实际用 `actor` 取代 `final class` 拿到并发安全
- [x] 5.2 实现 `func load(mediaId: Int, url: URL) async -> NSImage?`:先查缓存,miss 时 `DispatchQueue.global(qos: .userInitiated)` 读 `NSImage(contentsOf: url)`,成功写回缓存 — 用 `Task.detached(priority: .userInitiated)` 等价实现
- [x] 5.3 改造 `MediaLibraryView` 网格 cell:把 `AsyncImage(url: ...)` 替换为自定义 `LocalThumbView(media: Media)`,内部 `@State image: NSImage?` + `.task { image = await LocalImageLoader.shared.load(...) }`
- [x] 5.4 缺失文件占位图:文件不存在或加载失败时显示 SF Symbol `photo` 灰底卡片
- [ ] 5.5 滚动 500+ 项压测:cell 切出可视区不报警告(确认 NSCache 工作),内存稳定  **【MAC_TODO §2.3】**

## 6. 图片 / 视频详情视图

- [x] 6.1 新建 `MyNote/MyNote/MediaDetailView.swift`:接受 `Media` 参数,根据 `mime_type` 前缀分支
- [x] 6.2 图片分支:全屏 `Image(nsImage: NSImage(contentsOf: media.localFileURL!) ?? NSImage())`,加 ESC/点击关闭
- [x] 6.3 视频分支:`VideoPlayer(player: AVPlayer(url: media.localFileURL!))`,加播放/暂停/关闭
- [x] 6.4 `MediaLibraryView` 网格 cell 点击 → present `MediaDetailView`(sheet 或 fullScreenCover)
- [ ] 6.5 验证本地大图加载流畅;mp4 能播放(测试 H.264 与 HEVC)  **【MAC_TODO §2.2】**

## 7. QuickLook 集成(加分项)

- [ ] 7.1 新建 `MyNote/MyNote/QuickLookPreview.swift`:`NSViewControllerRepresentable` 包装 `QLPreviewPanel`,或用 `NSWindowController` 直接调 `QLPreviewPanel.shared().makeKeyAndOrderFront(nil)`  **【推迟到下一期】**
- [ ] 7.2 在 `MediaLibraryView` 加 `@State selectedMediaIndex: Int?` 跟踪选中项,cell 加 selection 状态  **【推迟到下一期】**
- [ ] 7.3 用 `.onKeyPress(.space)` 触发 QuickLook,数据源为当前 `media` 数组的 `localFileURL` 列表,initial index 为 `selectedMediaIndex`  **【推迟到下一期】**
- [ ] 7.4 实现 `QLPreviewPanelDataSource` + `QLPreviewPanelDelegate`,支持方向键切换上下张  **【推迟到下一期】**

> §7 整体推迟:QuickLook + SwiftUI 集成需要 NSResponder chain 控制,作为独立 change 实现更合适。MediaDetailView 的内嵌大图/视频已可覆盖主要 use case。

## 8. 清理 Message Feed 入口

- [ ] 8.1 从 Xcode `MyNote` target 移除 `FeedView.swift` 与 `FeedViewModel.swift`(文件保留在磁盘上做参考,不参与编译)  **【MAC_TODO §1.4 - Target Membership】**
- [x] 8.2 修改 `ContentView.swift`:导航直接展示 `MediaLibraryView`,删除任何指向 FeedView 的 tab/链接
- [x] 8.3 确认 `MyNoteApp.swift` 编译通过,无 dead imports — 由 MAC_TODO §2.1 启动验证

## 9. 收尾与文档

- [ ] 9.1 手动 QA:首次启动 → 选目录 → 看网格 → 滚动加载 → 切类型过滤 → 切星标过滤 → 点图片大图 → 点视频播放 → 空格 QuickLook  **【MAC_TODO §2.2,QuickLook 部分推迟】**
- [ ] 9.2 临时把 `MediaLibraryViewModel` 默认数据源换成 `APIMediaSource()` 再换回 `LocalMediaSource()`,验证切换工作正常(可走 1 次即可)  **【MAC_TODO §2.4】**
- [x] 9.3 在项目根目录 `开发日志/` 新建当日日志(按全局 workflow 规则),记录"Mac app 本地数据库化(第一期)" — `开发日志/2026-06-04.md`
- [x] 9.4 更新 `MyNote/README.md`(若存在)或在 `CLAUDE.md` 的 Architecture 节加一段说明 Mac 端的新架构:本地 GRDB 只读 + 共享 DATA_ROOT — 已加 `### Mac (MyNote/)` 段
- [ ] 9.5 commit 信息按惯例:`feat(mac): 本地 SQLite 直读 + 媒体网格原生化(第一期)`  **【MAC_TODO §5 - QA 后执行】**
