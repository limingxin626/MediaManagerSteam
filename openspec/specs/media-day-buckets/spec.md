# media-day-buckets Specification

## Purpose

定义 Media 页面以「天」为最小聚合单元的时间桶模型：包括后端 `/media/timeline` 的日级聚合契约、前端 bucket 的 key/cursor/边界约定、桶头视觉文案，以及 DateScrubber 日级跳转的落点规则。

## Requirements

### Requirement: Timeline 按天聚合
后端 `GET /media/timeline` SHALL 按 `(year, month, day)` 三元组聚合 `Media`（排除 `video_media_id IS NOT NULL` 的子片段），并按 `year DESC, month DESC, day DESC` 排序返回。响应每项 MUST 包含 `year: int`、`month: int`、`day: int`、`count: int` 四个字段。所有现有过滤参数（`starred`、`type`、`tag_id`、`actor_id`）SHALL 在分组前生效，行为与按月版本一致。

#### Scenario: 默认按天分组
- **WHEN** 数据库中 2026-05-29 有 7 条媒体、2026-05-28 有 3 条媒体
- **THEN** `GET /media/timeline` 响应数组中 MUST 包含 `{year:2026, month:5, day:29, count:7}` 和 `{year:2026, month:5, day:28, count:3}` 两项
- **AND** day=29 的项 MUST 排在 day=28 的项之前

#### Scenario: 仍排除视频子片段
- **WHEN** 某条 Media 的 `video_media_id` 不为 null（视频帧 / 章节）
- **THEN** 该条 MUST NOT 计入任何天的 `count`

#### Scenario: 过滤参数仍生效
- **WHEN** 调用 `GET /media/timeline?starred=true&type=image`
- **THEN** 仅 `starred=1` 且 `mime_type LIKE 'image/%'` 的媒体参与按天聚合
- **AND** 没有满足条件的天 MUST NOT 出现在响应中

### Requirement: 前端按天 bucket 模型
Media 页面浏览模式（非 Smart 搜索）SHALL 以「天」为虚拟滚动的最小桶单元。每个 bucket 的 key MUST 为 `YYYY-MM-DD` 格式字符串；bucket 起始 cursor MUST 为「次日 00:00:00 | 2147483647」以匹配 `/media` 端点的复合 cursor（`created_at|position` 倒序）契约。

#### Scenario: bucket key 为日期字符串
- **WHEN** timeline 返回 `{year:2026, month:5, day:29, count:7}`
- **THEN** 前端创建的 `BucketLayout.key` MUST 等于 `"2026-05-29"`

#### Scenario: bucket 边界判定按天
- **WHEN** 加载某天 bucket 时拉到一条 `created_at < 当天 00:00:00` 的 Media
- **THEN** 该条 MUST NOT 计入本 bucket
- **AND** 本 bucket 的 `status` MUST 标记为 `complete`，不再继续翻页

#### Scenario: 删除最后一项后该天消失
- **WHEN** 某天 bucket 仅剩 1 项，用户在预览中删除该项
- **THEN** 该 bucket 的 `count` 归零并从 timeline 中移除
- **AND** 该日期不再渲染桶头

### Requirement: 桶头显示完整日期
浏览模式下每个 bucket 的标题 SHALL 显示为「YYYY 年 M 月 D 日」中文格式，月份和日期 MUST NOT 补零（例如 `2026 年 5 月 9 日` 而非 `2026 年 05 月 09 日`）。

#### Scenario: 普通日期渲染
- **WHEN** bucket 为 `{year:2026, month:5, day:29}`
- **THEN** 桶头文本 MUST 完全等于 `2026年5月29日`

#### Scenario: 单数月与日不补零
- **WHEN** bucket 为 `{year:2026, month:3, day:7}`
- **THEN** 桶头文本 MUST 完全等于 `2026年3月7日`

### Requirement: DateScrubber 日级跳转
当用户在 DateScrubber 上拖动并释放到具体一天时，主网格 SHALL 定位到该天对应的 bucket 顶部（`headerOffset`），并触发该 bucket 的优先加载。若该天没有 bucket，定位到时间轴中第一个早于或等于该日期的 bucket。

#### Scenario: 跳转到存在的天
- **WHEN** 用户从 DateScrubber 释放在 2026-05-29 对应位置
- **THEN** 主滚动容器 `scrollTop` MUST 等于 `2026-05-29` bucket 的 `headerOffset`
- **AND** `loadBucketNow("2026-05-29")` MUST 被调用

#### Scenario: 跳转到不存在的天
- **WHEN** 用户跳转到 2026-05-15，但该日无媒体（timeline 中无此 bucket）
- **THEN** 落到 timeline 中第一个满足 `bucketDate <= 2026-05-15` 的 bucket
- **AND** 不抛出错误
