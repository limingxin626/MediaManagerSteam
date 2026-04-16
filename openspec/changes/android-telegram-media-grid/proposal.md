## Why

安卓消息流中多图排列效果不好——当前使用固定的计数-布局映射（2图并排、3图L型等），所有图片无论比例都分配相同权重，导致横图竖图混排时出现大量裁切和不自然的拉伸。Telegram 的分组图片布局根据每张图的宽高比动态计算布局，视觉效果更佳。

## What Changes

- 新增 Telegram 风格的 Mosaic 布局算法，根据图片宽高比动态决定行数、每行图片数量和每张图的尺寸权重
- 替换 `MessageCard.kt` 中的 `getGridLayout()` 固定映射和 `MediaThumbnailGrid` 的硬编码分支
- 单图保持现有逻辑不变（已根据比例自适应）
- 2-10 图使用新的动态布局算法
- 保留 "+N" 溢出显示逻辑

## Capabilities

### New Capabilities
- `mosaic-layout-algorithm`: Telegram 风格的 Mosaic 布局算法，输入图片宽高比列表，输出每行图片分配和尺寸权重

### Modified Capabilities

（无已有 spec 需要修改）

## Impact

- `android/app/src/main/java/com/example/myapplication/ui/components/MessageCard.kt`：重写 `MediaThumbnailGrid`、移除 `getGridLayout`/`GridLayoutSpec`，替换为动态布局
- 依赖 `Media.width` / `Media.height` 字段（已存在），缺失时 fallback 为 1:1
- 不影响后端、前端 Vue 或其他组件
