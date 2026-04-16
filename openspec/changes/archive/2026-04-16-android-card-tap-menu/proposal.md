## Why

当前安卓消息卡片使用长按触发上下文菜单（编辑/收藏/删除），但长按交互不够直观，用户发现率低。Telegram 的做法是点击卡片右侧空白区域即可弹出菜单，交互更自然、更易发现。

## What Changes

- 移除消息卡片的 `combinedClickable` 长按手势
- 在卡片右侧（元数据行右方的空白区域）添加一个可点击的隐形触发区，点击后弹出 `DropdownMenu`
- 菜单内容不变（编辑、收藏/取消收藏、删除）
- 保留单图卡片宽度自适应逻辑，确保右侧区域仍有足够的点击面积

## Capabilities

### New Capabilities
- `card-tap-menu`: 消息卡片点击右侧空白区域弹出上下文菜单的交互

### Modified Capabilities

## Impact

- `android/app/src/main/java/com/example/myapplication/ui/components/MessageCard.kt` — 主要修改文件，调整手势和菜单触发方式
