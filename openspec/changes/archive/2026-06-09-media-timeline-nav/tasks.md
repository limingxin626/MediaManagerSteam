## 1. 后端接口

- [x] 1.1 新增 `GET /media/timeline` 接口，使用 SQLite `strftime` 按月聚合媒体数量，支持 `type` 和 `starred` 过滤参数，返回 `[{year, month, count}]` 降序数组
- [x] 1.2 新增 `TimelineItem` Pydantic schema（year: int, month: int, count: int）

## 2. 前端时间轴组件

- [x] 2.1 创建 `TimelineBar.vue` 组件：垂直时间轴条，接收 `timeline` 数据和 `currentMonth` props，显示月份标签和数量，高亮当前月份，emit `jump` 事件
- [x] 2.2 移动端适配：屏幕宽度 < 768px 时显示精简模式（短月份标记）

## 3. 月份分隔头

- [x] 3.1 在 Media.vue 的 grid 渲染中，检测相邻 item 的月份变化，插入月份分隔头元素（跨整行宽度）

## 4. 跳转与滚动同步

- [x] 4.1 `useInfiniteScroll` 中新增 `jumpToCursor(cursor)` 方法：清空 items、设置 cursor、重新加载
- [x] 4.2 Media.vue 集成 TimelineBar，点击月份时调用 `jumpToCursor` 构造对应月份起始 cursor 跳转
- [x] 4.3 实现滚动位置同步：监听可视区域顶部 item 的 `created_at`，更新 `currentMonth` 传递给 TimelineBar

## 5. 过滤联动

- [x] 5.1 Media.vue 中 `type` 或 `starred` 过滤变化时，重新请求 `/media/timeline` 更新时间轴数据
