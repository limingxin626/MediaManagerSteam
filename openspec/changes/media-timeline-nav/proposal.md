## Why

Media 页面目前只能通过无限滚动浏览，无法快速跳转到特定时间段。当媒体数量较多时，用户找到某个时间段的内容需要大量滚动。需要一个类似 Telegram 媒体页、Windows 照片 app 的全局时间轴导航，让用户一键跳转到任意时间点。

## What Changes

- 新增后端接口 `GET /media/dates`，返回按月聚合的媒体数量分布，用于渲染时间轴
- Media 页面右侧添加垂直时间轴条，显示有媒体的月份标记
- 点击时间轴上的月份可跳转到对应时间段的媒体位置
- 滚动浏览时，时间轴上的当前位置指示器同步更新
- 媒体 grid 中插入日期分隔头（按月分组），便于定位

## Capabilities

### New Capabilities
- `timeline-nav`: 媒体页面全局时间轴导航组件，包含时间轴渲染、点击跳转、滚动同步

### Modified Capabilities

## Impact

- 后端新增 `/media/dates` 聚合查询接口
- 前端 `Media.vue` 需要集成时间轴组件和日期分组头
- `useApi.ts` 的 `useInfiniteScroll` 可能需要支持"跳转到指定 cursor"的能力
- 不影响现有分页逻辑，时间轴跳转复用现有 cursor 机制（direction=forward + cursor）
