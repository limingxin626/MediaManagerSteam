## Why

Media 页面当前按月聚合（一个 bucket = 一个月），月内媒体多时定位粒度不够细，月头滚动跨度大。改为按天聚合后，浏览节奏更接近 Apple Photos / Google Photos，用户跳到具体某天更直观。

## What Changes

- 后端 `GET /media/timeline` 在分组键中加入 `day`，返回 `{year, month, day, count}` 列表（DESC）。**BREAKING**：响应字段新增 `day`，老前端会忽略该字段（兼容），但若没有同步更新，bucket 仍按月渲染会丢失精度。
- `TimelineItem` Pydantic schema 增加 `day: int` 字段。
- 前端 `useVirtualGrid` 的 bucket 由「月」改为「天」：`bucketKey` → `YYYY-MM-DD`，相关 ISO 边界、`findBucketByDate`、`scrollToDate`、`currentDate` 全部按天精度工作。
- `Media.vue` 桶头文案：`YYYY年M月` → `YYYY年M月D日`；`timelineMin/MaxDate` 用日精度。
- DateScrubber 入参（timeline / min / max date）天然兼容更细粒度，本次不改其外部 API。

## Capabilities

### New Capabilities
- `media-day-buckets`: Media 页面按"天"聚合媒体的时间桶模型、桶头视觉，以及 `/media/timeline` 的日级聚合契约。

### Modified Capabilities
（无：`media-timeline` 描述 DateScrubber 的视觉/交互，未涉及聚合粒度，本次改动不修改其需求。）

## Impact

- 后端：`backend/app/routers/media.py` 的 `get_media_timeline`；`backend/app/schemas/media.py` 的 `TimelineItem`。
- 前端：`vue/src/composables/useVirtualGrid.ts`（核心）；`vue/src/views/Media.vue`（桶头文案、min/max date）。
- 性能：timeline payload 从 O(月份数) 增到 O(活跃天数)；每天 bucket 通常 1 个分页请求即完成，请求总数会增加，但单次更小，LAN 部署可接受。
- 视觉：稀疏日期会产生较多小桶头（每个 ~44px），垂直空白增多 — 已与用户确认接受。
