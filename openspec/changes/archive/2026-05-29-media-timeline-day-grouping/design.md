## Context

Media 页面当前以「月」为聚合粒度：后端 `/media/timeline` 用 `strftime('%Y', %m)` 分组，前端 `useVirtualGrid` 用 `YYYY-MM` 作 bucket key，桶头显示「YYYY 年 M 月」。月内媒体量大时一个 bucket 高度可达数千 px，定位 / 直觉跨度过粗，且 `bucketStartCursor` / `monthStartIso` 等所有边界逻辑都围绕「月」展开。本次将聚合粒度直接换成「天」，但保留现有的虚拟滚动 / dwell-loading / DateScrubber 集成不变。

## Goals / Non-Goals

**Goals:**
- 后端 timeline 输出按天分组，且仍按 `created_at` 降序。
- 前端 bucket 模型语义从「月」改「天」，最小侵入 `useVirtualGrid` 的并发加载、虚拟化与 scrubber 联动。
- 桶头文案改为「YYYY 年 M 月 D 日」。
- DateScrubber 拖动跳转仍能落到正确的 bucket（日级）。

**Non-Goals:**
- 不引入「月分组下嵌套天分组」的两级层次。
- 不修改 `/media` 列表分页 / 复合 cursor（`created_at|position`）契约。
- 不修改 `media-timeline` spec（DateScrubber 视觉/交互）的现有需求文本。
- 不引入按周 / 按年的可切换粒度选项。

## Decisions

### D1：日级聚合 in SQL，不在前端二次切桶
后端 `get_media_timeline` 增加 `day_col = func.cast(func.strftime('%d', Media.created_at), Integer)`，`group_by('year','month','day') order_by(year desc, month desc, day desc)`；返回 `TimelineItem(year, month, day, count)`。

**Why over alternative**：另一种做法是后端仍按月，前端拿到月聚合后请求该月全部 media 再二次切天 — 但会破坏现有 `loadBucketNow / dwell-load / 复合 cursor 分页`的流程，反而引入大量改动。日级聚合直接在 SQL 完成，对索引压力增量极小（SQLite 上 `created_at` 即便没函数索引，全表 strftime+group 在我们规模也是毫秒级）。

### D2：`bucketKey` = `YYYY-MM-DD`，`bucketStartCursor` 以「次日 00:00:00 | INT_MAX」开头
保持现有 cursor 语义：`/media` 用 `created_at|position` 复合 cursor 倒序分页。当天的起始 cursor 用「次日 00:00:00 | 2147483647」，触底判定改成「拉到的项 `created_at < 当天 00:00:00` 即 spilled」。

**Why**：和当前月级实现完全同构，最小改动。`nextDayStartIso(year, month, day)` 用 `new Date(year, month-1, day+1)` 让 JS 自动溢出处理跨月跨年。

### D3：`findBucketByDate` 改为日级线性查找
当前按月查找用 `b.year < y || (b.year===y && b.month <= m)`。改成 day 三元组比较：构造目标 `target = y*10000 + m*100 + d`，bucket key 同样可解析为整数比较；找第一个 `bucketInt <= target` 的 bucket。

`scrollToDate` 简化：既然 bucket 就是当天，落到 `b.headerOffset` 即可，不再需要按月内日期算 `frac`。

### D4：`currentDate` 仍返回 `Date`，但精度到天
`new Date(b.year, b.month-1, b.day)`。DateScrubber 的 `current-date` prop 接 Date，对它而言精度提升只是更准、不改格式。

### D5：保留 `monthHeaderH` 命名，仅语义换成「桶头高度」
不重命名，避免文件大面积 churn。可在 useVirtualGrid 顶部加一行短注释说明它现在度量的是「day header」。

## Risks / Trade-offs

- **垂直空白增加**：稀疏日期下每天 1–2 张图但占 ~44px 桶头 → 视觉密度下降。Mitigation：用户已确认接受；如未来想压缩可单独提一个空间优化 change。
- **timeline payload 增大**：从 O(月) → O(活跃天)。假设两年每天都有内容 ≈ 730 条，每条约 30 字节 JSON ≈ 22 KB，仍可一次性返回；LAN 部署无压力。如未来量级到「数千天」，可加 `since` 参数分段拉。Mitigation：当前规模不需要。
- **请求总数上升**：原本一个月一个 `/media` 请求（拉到 100 条即触底），现在一天一个请求。每个请求更小，但 HTTP 开销变多。Mitigation：`MAX_CONCURRENT=6` 仍生效；dwell 节流 + viewport-only dispatch 已限制实际触发量。
- **跨过 DST / 时区切换日的桶边界**：项目数据按 UTC ISO 字符串字典序比较 — 与现有月边界处理同源，本次不引入新风险。
- **老前端调用新后端**：响应多了 `day` 字段，老 TS 类型会忽略，运行不报错，但 UI 仍按月渲染会丢精度。Mitigation：后端 + 前端同 PR 上线。

## Migration Plan

1. 后端 schema + router 改动。
2. 前端 `useVirtualGrid` + `Media.vue` 同步改动。
3. 手动验证：
   - 桶头显示「YYYY 年 M 月 D 日」。
   - DateScrubber 拖动跳到「某月某日」，主网格滚动到对应桶。
   - 删除一项后该天 count 减 1，归零的天从 timeline 消失（已有 `removeItem` 逻辑覆盖）。
4. 无 DB 迁移、无破坏性持久化变更，回滚 = 还原两文件 + 一文件。
