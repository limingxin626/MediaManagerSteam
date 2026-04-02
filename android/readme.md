# MediaManager

一个 Android 媒体管理应用，支持消息、媒体、标签的本地存储与离线同步。

## 功能特性

- **消息列表**：Telegram 风格聊天界面，支持无限滚动（Paging3）、消息编辑、长按上下文菜单（编辑/收藏/删除）
- **#tag 解析**：发送消息时自动从文本中提取 `#xxx` 标签并关联，消息卡片内高亮显示
- **群组视图**：首页以 Telegram 风格列出每个 Tag 作为一个群组，点击进入标签过滤的消息列表
- **媒体管理**：缩略图网格浏览、全屏预览、收藏标记
- **收藏系统**：消息和媒体均支持收藏，缩略图右上角显示星标
- **离线同步**：基于 Outbox 模式，本地写入后入队，后台批量推送至后端

## 架构

**MVVM + Repository + Outbox 离线同步**

```
Compose Screen → ViewModel (StateFlow / PagingData)
    → Repository → DAO (Room / SQLite)
                 → SyncOutboxRepository → SyncPushService → POST /api/sync/apply
```

### 主要模块

| 目录 | 说明 |
|---|---|
| `ui/screens/` | 各页面：home、message、media、actor、tag、system |
| `ui/viewmodel/` | ViewModel，持有 StateFlow 和 PagingData |
| `ui/components/` | 复用组件：MessageCard、MediaCard 等 |
| `data/` | Room 实体、DAO、Repository、同步服务 |
| `navigation/` | Compose Navigation 路由定义 |

## 技术栈

- **语言**：Kotlin 2.0.21
- **UI**：Jetpack Compose + Material3 动态主题
- **数据库**：Room 2.6.1（版本 27，destructive migration）
- **分页**：Paging3 3.3.6
- **图片加载**：Coil 2.5.0
- **视频播放**：Media3 ExoPlayer 1.2.0
- **网络**：Retrofit 2.9.0 + Gson
- **DI**：手动单例（`DatabaseManager`）

## 构建

```bash
# 调试包
./gradlew assembleDebug

# 发布包
./gradlew assembleRelease

# 单元测试
./gradlew test

# 清理
./gradlew clean
```

> 需设置 `JAVA_HOME=C:/Program Files/Android/Android Studio/jbr`

## 文档

- [同步接口约定](docs/sync-apply-prompt.md)
- [消息设计说明](docs/message-design.md)
- [更新日志](docs/changelog/)
