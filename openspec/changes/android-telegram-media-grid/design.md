## Context

当前 Android 消息流中，多图布局使用固定的计数→布局映射（`getGridLayout`），所有图片在行内分配相同的宽度权重，不考虑图片实际宽高比。这导致横图和竖图混排时裁切严重，视觉效果差。

Telegram 的方案是根据每张图的 aspect ratio 动态计算最优行分配和尺寸权重，实现紧凑且视觉平衡的布局。

已有数据：`Media` 实体包含 `width` 和 `height` 字段，后端在 `process_file()` 时通过 ffprobe 提取并存储。

## Goals / Non-Goals

**Goals:**
- 实现 Telegram 风格的 Mosaic 布局算法，根据图片宽高比动态计算布局
- 2-10 张图使用动态算法，单图保持现有逻辑
- 保持 "+N" 溢出显示、视频标识、星标等现有功能不变
- 算法为纯计算函数，易于单元测试

**Non-Goals:**
- 不修改后端或 Vue 前端
- 不实现图片拖拽重排
- 不改变单图的布局逻辑

## Decisions

### 1. 算法实现方式：移植 Telegram 算法 vs 简化版

**选择：移植 Telegram 核心算法并简化**

Telegram 算法核心逻辑：
1. 将每张图的 aspect ratio 分类为 wide（>1.2）、narrow（<0.8）、square
2. 对 2-4 图使用启发式规则（根据比例组合选择横排/竖排/L型等）
3. 对 5+ 图使用优化搜索：遍历所有可能的行分配组合，按高度偏差评分，选最优解
4. 每行内按图片比例分配宽度权重

简化点：
- 不需要 avatar 偏移和 span 调整（我们不是聊天应用）
- 比例裁剪范围设为 [0.667, 1.7]（同 Telegram）
- 目标高度 = 容器宽度 × 1.33（同 Telegram 的 maxSizeWidth/3*4 逻辑）

**替代方案：** 使用 CSS flexbox 类似的简单行填充算法——放弃，因为 2-4 图场景的启发式规则是 Telegram 布局好看的关键。

### 2. 输出数据结构

算法输出 `MosaicLayout`：
```kotlin
data class MosaicLayout(
    val rows: List<MosaicRow>  // 每行包含图片索引和宽度比例
)
data class MosaicRow(
    val items: List<MosaicItem>,
    val heightRatio: Float  // 该行高度占总高度的比例
)
data class MosaicItem(
    val index: Int,        // 图片在原列表中的索引
    val widthRatio: Float  // 该图在行内的宽度比例（0-1）
)
```

### 3. Compose 渲染方式

使用 `SubcomposeLayout` 或基于权重的 `Row/Column` 组合：
- 总高度固定为容器宽度相关值（避免无限约束问题）
- 每行高度按 `heightRatio` 分配权重
- 行内每项按 `widthRatio` 分配权重

选择继续使用 `Row/Column` + `weight`，因为现有代码已经用此方式，改动最小。

## Risks / Trade-offs

- **[缺少宽高数据]** → 当 `width`/`height` 为 null 时，fallback 为 1:1 比例。老数据可能缺失维度信息，但效果不会比当前差。
- **[性能]** → 5+ 图的优化搜索遍历所有行分配组合，但组合数有限（最多几十种），计算量可忽略。使用 `remember` 缓存结果。
- **[布局跳动]** → 算法是纯计算，不依赖异步数据，不会产生布局跳动。
