## Context

当前 Android 应用底部导航有多个 tab（HOME, ACTORS, MEDIA, MESSAGES, SYSTEM_GALLERY, TAGS），其中 HOME 显示的是 GroupItem 标签分组列表，用户需要点击分组才能进入消息列表。这增加了到达核心内容（消息）的步骤。

当前导航路由定义在 `navigation/Navigation.kt` 的 `Routes` 对象和 `BottomNavDestination` 枚举中。底部导航栏通过 `BottomNavDestination` 控制。

## Goals / Non-Goals

**Goals:**
- 主页直接展示消息列表（无过滤条件，显示全部消息）
- 标签作为独立 tab，类似现有的演员列表页
- 底部导航调整为 4 个 tab：消息、标签、演员、媒体
- 设置入口移到消息页顶栏

**Non-Goals:**
- 不重新设计标签列表的 UI 样式（复用现有的 GroupItem 样式或类似演员列表的样式均可）
- 不修改消息列表本身的功能逻辑
- 不修改后端 API

## Decisions

### 1. 主页路由直接指向 MessageListScreen

将 `BottomNavDestination.HOME` 的 route 从 `Routes.HOME`（GroupItem 列表）改为 `Routes.MESSAGE_LIST` 的无过滤版本（tagId=-1）。这样打开 app 直接看到全部消息。

**替代方案**：保留 HomeScreen 作为壳页面嵌入 MessageListScreen → 增加不必要的层级，直接用 MessageListScreen 更简洁。

### 2. 标签页复用现有 HomeScreen 的 GroupItem 逻辑

现有 HomeScreen 已经按标签分组展示消息计数，改造为独立的 TagListScreen。可以直接复用 HomeViewModel 的数据逻辑，只是页面入口从主页移到标签 tab。

**替代方案**：从零做一个纯标签列表 → 丢失了现有的消息计数信息，体验更差。

### 3. 设置入口移到消息页顶栏右侧图标

底部导航腾出位置给标签 tab，设置作为低频操作移到顶栏齿轮图标。

### 4. 底部导航顺序

消息（主页）→ 标签 → 演员 → 媒体。消息作为最常用功能放在最左（主页位置）。

## Risks / Trade-offs

- **用户习惯变更**：现有用户（个人使用）需要适应新布局，影响极小
- **HomeScreen 复用**：将 HomeScreen 重命名/改造为 TagListScreen，需要确保 ViewModel 数据流不受影响
