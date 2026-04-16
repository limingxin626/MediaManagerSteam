## Context

当前 `MessageCard.kt` 使用 `combinedClickable(onLongClick)` 在整个卡片上监听长按来弹出 `DropdownMenu`。卡片底部元数据行使用 `Arrangement.SpaceBetween`，右侧仅在 starred 时显示星标图标，其余时候为空白。

## Goals / Non-Goals

**Goals:**
- 将菜单触发方式从长按改为点击卡片右侧空白区域
- 交互体验与 Telegram 一致

**Non-Goals:**
- 不改变菜单内容（编辑、收藏、删除）
- 不改变卡片布局、宽度自适应等其他逻辑

## Decisions

**方案：卡片外层用 Row 布局，右侧放置全高度的点击触发列**

将整个 `Card` 包裹在一个 `Row` 中：左侧是原有的卡片内容，右侧是一个与卡片等高的窄列（`Column`），作为菜单触发区域。

- 移除卡片级别的 `combinedClickable` 中的 `onLongClick`
- 外层 `Row` 结构：`[Card 内容] [触发列]`
- 触发列宽度固定（约 36-40dp），使用 `fillMaxHeight()` 与卡片等高
- 触发列整体 `.clickable { showMenu = true }`，底部放置三点图标（`Icons.Default.MoreVert`）
- `DropdownMenu` 锚定在触发列内

选择理由：Telegram 的交互是点击整个卡片右侧空白区域（不只是底部），需要触发区域覆盖卡片全高度。用 Row 包裹可以让右侧列自然与卡片等高，点击区域覆盖从顶部到底部的整个右侧。

## Risks / Trade-offs

- [卡片宽度需要减去触发列的宽度] → 触发列较窄（36-40dp），影响不大
- [移除长按后用户需要适应] → 三点图标在右侧底部提供视觉引导
