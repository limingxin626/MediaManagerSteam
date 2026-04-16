## ADDED Requirements

### Requirement: Aspect ratio classification
算法 SHALL 将每张图片的宽高比分类为三种类型：
- wide（宽图）：ratio > 1.2
- narrow（窄图/竖图）：ratio < 0.8
- square（方图）：0.8 ≤ ratio ≤ 1.2

当图片缺少宽高数据（width 或 height 为 null 或 0）时，SHALL fallback 为 ratio = 1.0（square）。

#### Scenario: 横图分类
- **WHEN** 图片宽高比为 1.5（如 1500x1000）
- **THEN** 分类为 "wide"

#### Scenario: 竖图分类
- **WHEN** 图片宽高比为 0.6（如 600x1000）
- **THEN** 分类为 "narrow"

#### Scenario: 缺少尺寸数据
- **WHEN** 图片 width 或 height 为 null
- **THEN** 使用默认比例 1.0，分类为 "square"

### Requirement: Two-image layout
当有 2 张图时，算法 SHALL 根据图片比例选择布局：
- 两张都是宽图且比例相近（差值 < 0.2）：上下排列（两行各一张）
- 否则：左右并排，宽度按各自比例分配

#### Scenario: 两张相似宽图
- **WHEN** 输入两张图，比例分别为 1.8 和 1.6
- **THEN** 布局为上下两行，每行一张，宽度均为 100%

#### Scenario: 一横一竖
- **WHEN** 输入两张图，比例分别为 1.5 和 0.7
- **THEN** 布局为一行两列，宽图占更大宽度比例

### Requirement: Three-image layout
当有 3 张图时，算法 SHALL 根据图片比例选择布局：
- 第一张为宽图：第一行放第一张，第二行并排放第二三张
- 第一张为窄图/方图：左侧放第一张，右侧上下排列第二三张（L型）

#### Scenario: 首图为宽图
- **WHEN** 输入三张图，第一张比例为 1.8，后两张为 0.9 和 1.1
- **THEN** 第一行放首图（全宽），第二行并排放后两张

#### Scenario: 首图为竖图
- **WHEN** 输入三张图，第一张比例为 0.6，后两张为 1.2 和 0.8
- **THEN** 左列放首图，右列上下排列后两张

### Requirement: Four-image layout
当有 4 张图时，算法 SHALL 根据图片比例选择布局：
- 第一张为宽图：第一行放第一张，第二行三列放剩余三张
- 否则：左侧放第一张，右侧三行各一张

#### Scenario: 首图为宽图
- **WHEN** 输入四张图，第一张比例为 2.0
- **THEN** 第一行放首图全宽，第二行三列放后三张

#### Scenario: 首图为方图
- **WHEN** 输入四张图，第一张比例为 1.0
- **THEN** 左列放首图，右列三行各一张

### Requirement: Five-plus image optimization
当有 5 张及以上图片时，算法 SHALL 使用优化搜索：
1. 将所有图片比例裁剪到 [0.667, 1.7] 范围
2. 遍历所有可能的行分配方案（1-4 行，每行最多 ceil(count/2) 张）
3. 对每种方案计算高度，按与目标高度的偏差评分
4. 选择得分最低的方案
5. 每行内按图片比例分配宽度

#### Scenario: 五张图优化布局
- **WHEN** 输入 5 张比例各异的图片
- **THEN** 算法输出 2-3 行的布局，每行图片数量和宽度由比例决定

#### Scenario: 十张图优化布局
- **WHEN** 输入 10 张图片
- **THEN** 算法输出 3-4 行的布局，总高度接近目标高度

### Requirement: Width proportional allocation
在每一行内，图片宽度 SHALL 按各自宽高比的比例分配，使得所有图片在行内具有相同的显示高度。

#### Scenario: 行内宽度分配
- **WHEN** 一行包含比例为 2.0 和 1.0 的两张图
- **THEN** 宽图占行宽的 2/3，方图占 1/3

### Requirement: Compose rendering integration
布局算法的结果 SHALL 通过 Compose 的 `Row`/`Column` + `weight` modifier 渲染，替换现有的 `RowBasedGrid` 和 `getGridLayout`。

#### Scenario: 渲染多图消息
- **WHEN** 消息包含 4 张不同比例的图片
- **THEN** `MediaThumbnailGrid` 使用动态算法计算布局并渲染，每张图显示大小与其比例匹配

#### Scenario: 保持现有功能
- **WHEN** 渲染带有视频、星标的多图消息
- **THEN** 视频播放图标、时长文字、星标标记正常显示在各自位置
