## ADDED Requirements

### Requirement: Thumbnail strip keeps current item centered

在 MediaPreview 弹层中，每当 `currentIndex` 改变，底部缩略图条 SHALL 把当前缩略图水平居中显示。

#### Scenario: Items 总宽小于容器宽
- **WHEN** `items` 的渲染总宽度 ≤ 缩略图条容器可视宽度
- **THEN** 缩略图条 SHALL 整体居中显示，且不出现水平滚动条
- **AND** 当前项以放大/高亮样式标识，不需要滚动

#### Scenario: Items 总宽大于容器宽，切换到中段项
- **WHEN** 总宽超过容器宽，用户切换到中段某一项（前后均有可见缩略图空间）
- **THEN** 该项 SHALL 水平居于容器视口的几何中点（容差 ≤ 2px）
- **AND** 滚动 SHALL 带平滑过渡

#### Scenario: 切换到首项或末项
- **WHEN** 用户切换到 `items[0]` 或 `items[last]` 且总宽超过容器宽
- **THEN** 缩略图条 SHALL 滚动到内容起点或终点；当前项可能不在几何正中，但 SHALL 完整可见且高亮

#### Scenario: 通过点击缩略图切换
- **WHEN** 用户点击非当前项的缩略图
- **THEN** `currentIndex` SHALL 更新为该项
- **AND** 缩略图条 SHALL 在动画过渡中把该项滚动到容器中心（按上述规则）

### Requirement: Main media transitions with direction on navigation

主预览区的图片或视频 SHALL 在切换时以带方向感的进入/退出动画过渡，而非瞬时替换。

#### Scenario: 向后翻页（next）
- **WHEN** 用户点击右箭头、按 ArrowRight/ArrowDown，或点击 `currentIndex` 之后的缩略图
- **THEN** 当前媒体 SHALL 向左淡出，新媒体 SHALL 从右侧滑入
- **AND** 整个过渡时长 SHALL 在 150–250ms 之间
- **AND** 同一时刻至多只有一个 `<video>` 元素被挂载，避免重复播放

#### Scenario: 向前翻页（prev）
- **WHEN** 用户点击左箭头、按 ArrowLeft/ArrowUp，或点击 `currentIndex` 之前的缩略图
- **THEN** 当前媒体 SHALL 向右淡出，新媒体 SHALL 从左侧滑入
- **AND** 时长与对称性与向后翻页一致

#### Scenario: 同位刷新不触发动画
- **WHEN** 因 replace、tag 变更等导致当前项数据更新但 `id` 未变
- **THEN** 主预览区 SHALL NOT 触发滑动动画（仅按需刷新 src）

#### Scenario: 关闭弹层不触发滑动
- **WHEN** 用户关闭 MediaPreview
- **THEN** 关闭使用原有 fade 过渡，SHALL NOT 触发滑动方向动画
