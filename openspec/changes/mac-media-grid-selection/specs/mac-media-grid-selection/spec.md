## ADDED Requirements

### Requirement: Single click selects without opening preview

在 Mac 端 `MediaLibraryView` 的网格中，单击某项 SHALL 仅将其设为「选中」，不打开预览。

#### Scenario: Click an unselected item

- **WHEN** 用户在网格中单击一个当前未选中的项
- **THEN** 该项 SHALL 被设为 `selectedIndex`
- **AND** 该项 SHALL 以可视方式高亮（蓝色描边或等价 selection ring）
- **AND** 预览 sheet SHALL NOT 被打开

#### Scenario: Click the already-selected item

- **WHEN** 用户单击当前已选中的项
- **THEN** `selectedIndex` SHALL 保持不变
- **AND** 预览 sheet SHALL NOT 被打开

#### Scenario: Single click on item B while item A is selected

- **WHEN** 用户已选中 A，再单击 B
- **THEN** B SHALL 变为选中态，A SHALL 不再选中
- **AND** 同一时刻 SHALL 只有 0 个或 1 个选中项

### Requirement: Double click opens preview

在 Mac 端 `MediaLibraryView` 的网格中，双击某项 SHALL 打开该项的预览。

#### Scenario: Double click an item

- **WHEN** 用户在网格中双击一个项（两次点击间隔在系统 `NSEvent.doubleClickInterval` 内）
- **THEN** 预览 sheet SHALL 打开
- **AND** `MediaDetailView` 的 `currentIndex` SHALL 等于被双击项的索引
- **AND** 被双击项 SHALL 同时成为网格的 `selectedIndex`

### Requirement: Arrow keys move selection within the grid

当网格视图持有键盘焦点时，按方向键 SHALL 在网格内移动选中项。

#### Scenario: Right arrow moves to next item

- **WHEN** 网格持焦，已有 `selectedIndex`，按 → 键
- **THEN** `selectedIndex` SHALL 加 1
- **AND** 若已是最后一项，SHALL 保持不变（不 wrap-around）

#### Scenario: Left arrow moves to previous item

- **WHEN** 网格持焦，已有 `selectedIndex`，按 ← 键
- **THEN** `selectedIndex` SHALL 减 1
- **AND** 若已是第 0 项,SHALL 保持不变(不 wrap-around)

#### Scenario: Down arrow moves to item one row below

- **WHEN** 网格持焦,已有 `selectedIndex`,按 ↓ 键,且网格列数为 N
- **THEN** `selectedIndex` SHALL 加 N
- **AND** 若加 N 后超过最后一项索引,SHALL 被夹到 (count - 1)

#### Scenario: Up arrow moves to item one row above

- **WHEN** 网格持焦,已有 `selectedIndex`,按 ↑ 键,且网格列数为 N
- **THEN** `selectedIndex` SHALL 减 N
- **AND** 若减 N 后小于 0,SHALL 被夹到 0

#### Scenario: Arrow key with no current selection

- **WHEN** 网格持焦,`selectedIndex` 为 nil,且 `media` 非空,按任一方向键
- **THEN** `selectedIndex` SHALL 被设为 0

#### Scenario: Selection moves out of viewport

- **WHEN** 方向键导致 `selectedIndex` 指向的项当前不在 ScrollView 可视区域
- **THEN** ScrollView SHALL 自动滚动,使该项进入可视区域(尽量居中,使用 `anchor: .center`)

### Requirement: Spacebar toggles preview

当网格视图持有键盘焦点或预览 sheet 处于打开状态时,按空格键 SHALL 切换预览的打开/关闭。

#### Scenario: Space opens preview for selected item

- **WHEN** 网格持焦,预览 sheet 未打开,`selectedIndex` 非空,按空格键
- **THEN** 预览 sheet SHALL 打开,`currentIndex` 等于 `selectedIndex`

#### Scenario: Space opens first item when nothing selected

- **WHEN** 网格持焦,预览 sheet 未打开,`selectedIndex` 为 nil,`media` 非空,按空格键
- **THEN** `selectedIndex` SHALL 被设为 0
- **AND** 预览 sheet SHALL 打开,`currentIndex` 等于 0

#### Scenario: Space closes the open preview

- **WHEN** 预览 sheet 已打开,按空格键
- **THEN** 预览 sheet SHALL 关闭
- **AND** 关闭后,网格的 `selectedIndex` SHALL 等于预览关闭时的 `currentIndex`(便于用户接着从那张图继续浏览)

#### Scenario: Space with empty media list

- **WHEN** `media` 为空,按空格键
- **THEN** 预览 sheet SHALL NOT 被打开,且不报错

### Requirement: Default selection on first load

网格首次加载完成后,SHALL 默认选中第 0 项,使后续方向键操作有起始位置。

#### Scenario: Initial load completes with items

- **WHEN** `MediaLibraryView` 首次出现,`loadInitial()` 完成且 `media` 非空
- **THEN** `selectedIndex` SHALL 被设为 0

#### Scenario: Initial load returns empty

- **WHEN** `loadInitial()` 完成但 `media` 为空
- **THEN** `selectedIndex` SHALL 保持为 nil

#### Scenario: Filter change reloads list

- **WHEN** 用户切换媒体类型筛选或星标筛选,触发 `loadInitial()` 重新加载
- **THEN** 加载完成后 `selectedIndex` SHALL 被设为 0(若新结果非空)或 nil(若为空)

### Requirement: Selection ring styling

选中项 SHALL 以视觉可辨的 selection ring 标识,贴近 macOS Finder/Photos 的标准样式。

#### Scenario: Selected item is visually distinct

- **WHEN** 某项的索引等于 `selectedIndex`
- **THEN** 该项 SHALL 显示蓝色描边(或等价的系统 accent color 描边),线宽 ≥ 2pt
- **AND** 描边 SHALL 围绕缩略图四周,不遮挡缩略图本身的主体内容
- **AND** 已有的「视频播放图标」「星标」徽标 SHALL 继续可见,不被 selection ring 遮挡
