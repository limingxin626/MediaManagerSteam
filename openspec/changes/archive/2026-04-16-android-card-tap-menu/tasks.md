## 1. 移除长按手势

- [x] 1.1 移除 `MessageCard` 的 `combinedClickable` 中的 `onLongClick` 回调

## 2. 添加卡片右侧全高度触发列

- [x] 2.1 将卡片包裹在 `Row` 中，右侧添加与卡片等高的 `Column`（约 36-40dp 宽），整体可点击触发 `showMenu = true`
- [x] 2.2 在触发列底部添加 `MoreVert` 三点图标作为视觉提示
- [x] 2.3 将 `DropdownMenu` 锚定到触发列内

## 3. 验证

- [x] 3.1 编译运行，验证点击三点图标弹出菜单、菜单功能正常、长按不再触发菜单
