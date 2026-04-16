## 1. 核心算法

- [x] 1.1 新建 `MosaicLayout.kt` 文件（在 `ui/components/` 下），定义数据结构 `MosaicLayout`、`MosaicRow`、`MosaicItem`
- [x] 1.2 实现 `calculateMosaicLayout(ratios: List<Float>): MosaicLayout` 纯函数，包含：比例分类、2-4图启发式规则、5+图优化搜索
- [x] 1.3 实现行内宽度按比例分配逻辑

## 2. Compose 渲染集成

- [x] 2.1 在 `MessageCard.kt` 中新建 `MosaicRowsGrid` 和 `MosaicLeftColumnGrid` composable，用 `Row/Column` + `weight` 渲染
- [x] 2.2 修改 `MediaThumbnailGrid`：2-10图分支调用 `calculateMosaicLayout` + Mosaic 渲染器
- [x] 2.3 保留 "+N" 溢出、视频标识、星标等现有功能（`OverflowCell` 组件）
- [x] 2.4 删除废弃的 `GridLayoutSpec`、`getGridLayout()`、`RowBasedGrid()` 代码

## 3. 验证

- [x] 3.1 构建通过（`./gradlew assembleDebug`）
- [ ] 3.2 在设备上测试不同图片数量和比例组合的显示效果
