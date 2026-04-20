## Context

消息界面 (`Message.vue`) 采用类聊天布局：最新消息在底部，向上滚动加载历史。已有双向分页（`topSentinel` 加载更早、`bottomSentinel` 加载更新）和浮动日期徽章。后端已有 `GET /messages/dates?year=&month=` 接口返回每月消息分布，以及 `direction=forward` 分页支持。项目已安装 `v-calendar` 依赖但未使用。

## Goals / Non-Goals

**Goals:**
- 点击顶部浮动日期徽章弹出日历面板，快速跳转到任意有消息的日期
- 日历上标记有消息的日期（圆点），无消息日期不可选
- 跳转后从目标日期的消息开始显示，可双向滚动

**Non-Goals:**
- 不做搜索功能
- 不改变现有的无限滚动行为
- 不做日期范围筛选

## Decisions

1. **日历组件：使用 v-calendar**
   - 已在项目依赖中，功能完善（attributes 可标记日期、支持深色主题）
   - 替代方案：自定义日历组件 → 开发量大，不值得

2. **跳转实现：传入目标日期 ISO 字符串作为 cursor**
   - 后端 cursor 是 `created_at.isoformat()`，传入 `YYYY-MM-DDT00:00:00` 即可定位到该日期
   - 使用已有的默认降序分页获取该日期及之前的消息，然后设置 `forwardCursor` 启用向下加载更新消息
   - 替代方案：新增专用 API → 过度设计，现有 cursor 机制已满足

3. **日历数据获取：调用已有 `/messages/dates` 接口**
   - 日历切换月份时按需加载，缓存已加载的月份数据
   - 替代方案：一次加载所有月份 → 数据量不确定，按需更好

4. **弹窗样式：Popover 浮层，非全屏 Modal**
   - 轻量，点击日期徽章弹出，选择后自动关闭
   - 与现有 HeadlessUI 风格一致

## Risks / Trade-offs

- [跳转后消息数量少] → 初始加载使用较大 limit（如 20），确保有足够上下文
- [月份切换频繁请求] → 缓存已加载月份数据到 Map 中
