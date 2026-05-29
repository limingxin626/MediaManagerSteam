## 1. 后端：timeline 按天聚合

- [x] 1.1 `backend/app/schemas/media.py`：在 `TimelineItem` 上新增 `day: int` 字段
- [x] 1.2 `backend/app/routers/media.py:get_media_timeline`：增加 `day_col = func.cast(func.strftime('%d', Media.created_at), Integer)`，加入 `select` 列、`group_by('year','month','day')`、`order_by(year desc, month desc, day desc)`
- [x] 1.3 返回时构造 `TimelineItem(year=r.year, month=r.month, day=r.day, count=r.count)`
- [ ] 1.4 手动验证：`curl /media/timeline | head` 看到 `day` 字段且按天分组、最新天在前

## 2. 前端：useVirtualGrid 切换到日级 bucket

- [x] 2.1 `vue/src/composables/useVirtualGrid.ts`：`TimelineEntry` 新增 `day: number`
- [x] 2.2 把 `bucketKey(year, month)` 改为 `bucketKey(year, month, day)`，返回 `YYYY-MM-DD`
- [x] 2.3 用 `dayStartIso(y,m,d)` / `nextDayStartIso(y,m,d)` 替换 `monthStartIso` / `nextMonthStartIso`；`nextDayStartIso` 用 `new Date(y, m-1, d+1)` 让 JS 自动处理跨月跨年
- [x] 2.4 `bucketStartCursor` 改用「次日 00:00:00 | 2147483647」
- [x] 2.5 `buckets` computed 改为遍历 `timeline` 每个 `{year, month, day}` 项构造 `BucketLayout`，并在 `BucketLayout` 类型上加 `day: number`
- [x] 2.6 `runLoad` 中的 `monthStart` 改为 `dayStart`，spilled 判定 `m.created_at < dayStart` 不变
- [x] 2.7 `findBucketByDate(date)`：按 `y*10000+m*100+d` 整数比较查找首个 `<= target` 的 bucket
- [x] 2.8 `scrollToDate`：直接定位到 `b.headerOffset`，删除原月内 `frac` 计算
- [x] 2.9 `currentDate`：用 `new Date(b.year, b.month-1, b.day)`
- [x] 2.10 `removeItem` 内查找 timeline 项的等式：用 `bucketKey(t.year, t.month, t.day)` 比较
- [x] 2.11 `scrollToBucket(year, month)` 签名加 `day` 参数，调用方一并改

## 3. 前端：Media.vue 桶头与边界日期

- [x] 3.1 `vue/src/views/Media.vue` 桶头模板：`{{ b.year }}年{{ b.month }}月{{ b.day }}日`
- [x] 3.2 `timelineMinDate`：`new Date(last.year, last.month-1, last.day)`
- [x] 3.3 `timelineMaxDate`：`new Date(first.year, first.month-1, first.day, 23, 59, 59)`
- [x] 3.4 `handleDateScrubberJumpFinal` 内 `loadBucketNow` 的 key 用新 `bucketKey(target.year, target.month, target.day)`

## 4. 联调与回归

- [ ] 4.1 启动后端 `python api.py`、前端 `pnpm dev`，浏览器打开 `/media`
- [ ] 4.2 验证 golden path：滚动主网格，桶头显示「YYYY 年 M 月 D 日」
- [ ] 4.3 验证 DateScrubber：拖动到某天，气泡显示该天，释放后主网格定位到对应桶顶部
- [ ] 4.4 验证过滤器（type=video / image、starred、tag、actor）切换后 timeline 仍按天聚合
- [ ] 4.5 验证删除：删某天最后一项，桶头消失
- [ ] 4.6 验证 Smart 搜索模式不受影响（不渲染 timeline / DateScrubber）

## 5. 收尾

- [x] 5.1 `pnpm build` 通过 vue-tsc 类型检查
- [x] 5.2 写当日开发日志（`开发日志/2026-05-29.md`）：记录改动与验证结果
