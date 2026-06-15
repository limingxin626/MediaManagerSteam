# Mac 端手动操作清单

以下任务需要在 Mac 上的 Xcode GUI / 实机运行环境完成,Windows 侧无法代劳。按顺序执行。

---

## 1. Xcode 工程配置(必做,否则编译不过)

### 1.1 添加 GRDB.swift SPM 依赖

1. 在 Xcode 打开 `MyNote/MyNote.xcodeproj`
2. 菜单 **File → Add Package Dependencies...**
3. URL 框输入:`https://github.com/groue/GRDB.swift`
4. Dependency Rule 选 **Up to Next Major Version**,默认起始版本 `6.0.0`(推荐 v6 最新)
5. 点 **Add Package**
6. 在出现的 product 列表勾选 **GRDB**,Target 选 `MyNote`
7. 点 **Add Package** 完成

验证:`File → Packages → Resolve Package Versions` 不报错。

### 1.1.5 添加 swift-markdown-ui SPM 依赖(2026-06-08 新增)

消息正文 markdown 渲染依赖此包。**不加 app 会编不过**(`MarkdownBody.swift` import 失败)。

1. 在 Xcode 菜单 **File → Add Package Dependencies...**
2. URL 框输入:`https://github.com/gonzalezreal/swift-markdown-ui`
3. Dependency Rule 选 **Up to Next Major Version**,起始版本 `2.4.1`(2024-10 发布,最后稳定版)
4. 点 **Add Package**
5. 在 product 列表勾选 **MarkdownUI**,Target 选 `MyNote`
6. 点 **Add Package** 完成

说明:swift-markdown-ui 作者已把新开发迁去 [Textual](https://github.com/gonzalezreal/textual),
此包进入 maintenance mode,但 GFM 全特性已稳定可用,继续作为我们的方案。


### 1.2 设置 macOS Deployment Target ≥ 14.0

1. 在 Project Navigator 点 `MyNote` 蓝色工程图标
2. 选 TARGETS → MyNote → **General** tab
3. Minimum Deployments → macOS 改为 **14.0** 或更高
4. 同样去 PROJECT → MyNote → **Info** tab 确认 deployment target

理由:NSImage 原生 webp 解码需要 macOS 14+。

### 1.3 把新文件加入 target

新建的 Swift 文件需要在 Xcode 里 "Add Files to MyNote",并勾选 `MyNote` target:

- `Settings.swift`
- `DataRootPicker.swift`
- `LocalDatabase.swift`
- `MediaRecord.swift`
- `MediaRepository.swift`
- `MediaSource.swift`
- `LocalImageLoader.swift`
- `LocalThumbView.swift`
- `OnboardingView.swift`
- `MediaDetailView.swift`(替换/新增,看是否已在工程中)
- `NSScrollViewBridge.swift`(**2026-06-07 新增**,DateScrubber-fix 用)

做法:在 Project Navigator 右键 `MyNote` 文件夹 → **Add Files to "MyNote"...** → 多选上述文件 → 勾 `MyNote` target → Add。

### 1.4 从 target 移除 FeedView / FeedViewModel(可选但推荐)

第一期不用 message feed。两种做法:

- **保留文件但不参与编译**:在 Project Navigator 选中 `FeedView.swift` / `FeedViewModel.swift`,右侧 File Inspector → Target Membership 取消勾选 `MyNote`
- **直接删除**:选中文件按 Delete → **Remove Reference**(保留磁盘文件)

如果不做这步,编译会因 `ContentView` 不再引用 `FeedView` 而正常通过,但工程里多两个 dead 文件。

### 1.5 Entitlements 检查文件系统访问

打开 `MyNote/MyNote/MyNote.entitlements`,确认:

- 如果开启了 App Sandbox(`com.apple.security.app-sandbox = true`),需要加 **User Selected File** 权限:
  - `com.apple.security.files.user-selected.read-only = true`
- 第一期建议先**关掉 sandbox**(`app-sandbox = false`),省去 security-scoped bookmark 的复杂度。等以后准备上 Mac App Store 再处理。

---

## 2. 首次运行验证

### 2.1 启动 app

`Cmd+R` 运行。预期:

1. 出现 OnboardingView,显示"欢迎使用 MyNote" + "选择数据目录"按钮
2. 点击按钮,弹出 NSOpenPanel
3. 选择 backend 的 DATA_ROOT 目录(里面有 `db.sqlite3` + `thumbs/` + `uploads/`)
4. 点确定后,主界面切换到媒体网格
5. Xcode console 应有打印:`✅ LocalDatabase opened. media count = NNN at /path/...`

### 2.2 主界面 QA(对应 tasks.md 9.1)

- [ ] 媒体网格能显示缩略图(4 列)
- [ ] 滚动到底部自动加载下一页(loadMore 触发,有 ProgressView)
- [ ] 点"图片"按钮 → 只显示 image
- [ ] 点"视频"按钮 → 只显示 video
- [ ] 点"全部"按钮 → 全显示
- [ ] 点右上角星标 → 只显示已收藏
- [ ] 点某张图片 → 弹出 MediaDetailView,显示大图
- [ ] 点某个视频 → 弹出 MediaDetailView,内嵌 AVPlayer 能播放
- [ ] ESC 键关闭详情视图
- [ ] 工具栏"更换数据目录"按钮工作正常(选择新目录后 app 重启)

### 2.3 滚动压测(对应 5.5)

滚动到 500+ 项,观察:

- [ ] 滚动流畅,无明显卡顿
- [ ] Xcode Memory gauge 稳定,不持续上涨(NSCache 工作正常)

### 2.4 数据源切换验证(对应 9.2)

可选回退验证:

1. 编辑 `MediaLibraryViewModel.swift`,把默认参数从 `LocalMediaSource()` 改为 `APIMediaSource()`
2. 启动 backend(`cd backend && python api.py`)
3. 运行 app,验证走 HTTP 路径也能工作
4. 改回 `LocalMediaSource()`

---

## 3. 错误场景验证(快速过一遍)

### 3.1 DATA_ROOT 目录被删

1. 配置好后退出 app
2. 重命名 DATA_ROOT 目录
3. 启动 app → 预期回到 OnboardingView,显示错误提示

### 3.2 选错目录(没有 db.sqlite3)

1. 启动后选一个空目录
2. 预期:错误提示"未找到数据库文件: ..."

### 3.3 schema 不匹配

无法快速复现,跳过。

---

## 4. 后续阶段(本次 spec 范围外)

延后到下一个 OpenSpec change:

- **QuickLook 集成**(原 tasks 7.x):空格键预览。需要 NSResponder chain 控制,代码量不小,作为独立 change 更合适
- 写操作(starred toggle 等):暂时通过 HTTP 路径,UI 上已隐藏入口
- Message feed 视图本地化
- Spotlight 索引、Share 扩展、Photos 框架导入

---

## 5. 提交

QA 全过后:

```bash
git add -A
git commit -m "feat(mac): 本地 SQLite 直读 + 媒体网格原生化(第一期)"
```

(具体 commit 信息见 `开发日志/`)
