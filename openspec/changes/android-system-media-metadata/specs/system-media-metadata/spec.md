## ADDED Requirements

### Requirement: Local-only metadata persistence

应用 SHALL 将系统媒体收藏和标签关系保存在本机 Room 中，并 SHALL NOT 修改 MediaStore、复制文件、上传或加入同步 Outbox。

#### Scenario: 收藏系统图片
- **WHEN** 用户收藏某个系统图片
- **THEN** `system_media_metadata` 保存该 stableKey 的收藏状态
- **AND** 不产生 backend 请求或 Outbox 项

### Requirement: Existing tags are reused

系统媒体 SHALL 通过独立 junction 表关联现有 `Tag`，不得写入现有 `media_tag`。

#### Scenario: 添加多个标签
- **WHEN** 用户为系统媒体选择多个标签
- **THEN** junction 表保存每个 stableKey/tagId 关系
- **AND** 原 Room Media 标签关系不受影响

### Requirement: List and preview metadata consistency

Media 网格和系统媒体预览 SHALL 显示同一 Room 元数据状态，并在修改后即时更新。

#### Scenario: 在预览中收藏
- **WHEN** 用户在预览中切换收藏
- **THEN** 预览收藏图标立即变化
- **AND** 返回网格后该媒体保持收藏状态

### Requirement: Tag editing

用户 SHALL 能从系统媒体 UI 查看当前标签，并通过现有标签选择器添加或移除标签。

#### Scenario: 保存标签选择
- **WHEN** 用户确认新的标签集合
- **THEN** 该系统媒体的 tag links 被原子替换

### Requirement: Favorite and tag filtering

Media 页面 SHALL 支持仅显示已收藏项目，以及按一个标签筛选；两个筛选同时启用时 SHALL 使用交集。

#### Scenario: 组合筛选
- **WHEN** 用户启用收藏筛选并选择标签 A
- **THEN** 页面仅显示同时已收藏且带标签 A 的系统媒体
