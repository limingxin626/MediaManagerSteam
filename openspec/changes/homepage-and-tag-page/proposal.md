## Why

打开 app 最常做的事是查看最新消息，但现在主页是标签分组列表，需要多点一步才能进入消息列表。标签和演员本质上都是分类维度，应该放在同级。主页直接展示消息列表能减少操作步骤，提升体验一致性。

## What Changes

- 主页（HOME）从标签分组列表改为消息列表（当前的 MessageListScreen，无过滤条件）
- 新增独立的标签页（TAG_LIST），展示所有标签，点击进入按标签过滤的消息列表
- 底部导航栏改为 4 个标签：消息（主页）、标签、演员、媒体
- 设置入口移到顶栏或消息页菜单中
- 移除原有的 HomeScreen（GroupItem 分组列表）

## Capabilities

### New Capabilities
- `tag-list-page`: 独立的标签列表页面，展示所有标签及消息计数，点击导航到按标签过滤的消息列表

### Modified Capabilities
（无已有 spec 需要修改）

## Impact

- Android 导航结构：Routes、NavGraph、底部导航栏配置
- 移除 HomeScreen 及 HomeViewModel
- MessageListScreen 成为主页入口（无过滤条件时显示全部消息）
- 底部导航栏 tab 数量和图标调整
- 设置页面入口位置变更
