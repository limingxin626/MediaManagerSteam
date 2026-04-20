## Why

消息界面打开时从最新消息开始显示，想看较早的消息需要一直向上滑动，非常不方便。需要一个日期跳转功能，点击即可直达某天的消息。

## What Changes

- 顶部浮动日期徽章变为可点击，点击后弹出日历面板
- 日历面板显示有消息的日期（圆点标记），选中日期后跳转到该日期的消息
- 利用已有的 `GET /messages/dates` 后端接口获取每月消息分布
- 利用已有的 `direction=forward` 双向分页能力加载目标日期的消息

## Capabilities

### New Capabilities
- `date-jump-calendar`: 日历弹窗 UI 组件及日期跳转交互逻辑

### Modified Capabilities

（无需修改已有 spec）

## Impact

- 前端：`Message.vue` 增加日历弹窗交互，可能使用 `v-calendar` 或自定义日历组件
- 后端：可能需要微调 `/messages/with-detail` 接口以支持按日期定位（传入日期作为 cursor）
- 依赖：可能新增或启用 `v-calendar` 依赖
