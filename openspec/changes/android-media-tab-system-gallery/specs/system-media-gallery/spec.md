## ADDED Requirements

### Requirement: Media tab uses accessible system media

Android 底部导航“媒体”页面 SHALL 从设备 MediaStore 读取应用当前可访问的图片和视频，而不是从 Room `media` 表生成列表。读取行为 SHALL NOT 上传、复制或持久化媒体记录。

#### Scenario: 打开已授权的媒体页
- **WHEN** 用户打开“媒体”页且应用拥有图片和视频读取权限
- **THEN** 页面显示 MediaStore 中可访问的全部图片和视频
- **AND** 不向 Room 写入 `Media` 记录，也不发起 backend 请求

#### Scenario: Android 14 部分媒体授权
- **WHEN** 系统只授予用户选择的部分照片和视频访问权
- **THEN** 页面仅显示系统允许应用访问的项目
- **AND** 不把不可访问项目视为加载错误

### Requirement: Version-aware and partial permission handling

媒体页 SHALL 根据 Android 版本请求和检查媒体读取权限。Android 13+ SHALL 分别处理图片与视频权限；Android 12 及以下 SHALL 使用外部存储读取权限。仅授权一种媒体类型时，页面 SHALL 继续显示该类型。

#### Scenario: 仅授予图片权限
- **WHEN** 应用获得图片读取权限但未获得视频读取权限
- **THEN** 页面加载并显示可访问图片
- **AND** 不因视频权限缺失阻止整个页面

#### Scenario: 权限完全未授予
- **WHEN** 应用没有任何可用的媒体读取权限
- **THEN** 页面显示权限说明和可触发系统授权请求的操作
- **AND** 不查询需要未授予权限的 MediaStore collection

#### Scenario: 用户拒绝授权
- **WHEN** 用户拒绝媒体权限请求
- **THEN** 页面保持无权限状态
- **AND** 不自动重复弹出授权请求

### Requirement: Unified chronological ordering

图片和视频 SHALL 合并为一个列表，并按 `dateModified` 从新到旧排序。排序结果 SHALL 对相同时间值保持稳定。

#### Scenario: 图片和视频混合排序
- **WHEN** 最近修改的视频比某张图片更新
- **THEN** 视频显示在该图片之前

### Requirement: Collision-free system media identity

每个系统媒体项目 SHALL 使用包含 collection 类型和 MediaStore ID 的复合身份，或等价的完整 content URI。Compose item key、点击事件和详情定位 SHALL NOT 只使用数字 ID。

#### Scenario: 图片和视频拥有相同数字 ID
- **WHEN** MediaStore 图片与视频的 `_ID` 都为 42
- **THEN** 两个项目拥有不同的列表 key
- **AND** 点击任一项目均打开对应的正确媒体

### Requirement: Existing Media page presentation is retained

页面 SHALL 保持现有 Media 页的三列网格、顶部视觉结构和滚动时底部导航显隐行为。网格 SHALL 通过 `content://` URI 加载系统缩略图，并 SHALL 显示视频类型标识和可用时长。

#### Scenario: 渲染系统图片
- **WHEN** 网格项目是图片
- **THEN** 页面显示该图片的 MediaStore 缩略图

#### Scenario: 渲染系统视频
- **WHEN** 网格项目是视频
- **THEN** 页面显示视频缩略图、视频标识和格式化时长

#### Scenario: Room 专属筛选不可用
- **WHEN** Media 页的数据源为系统媒体且没有 Room 星标或标签状态
- **THEN** 页面不显示会产生虚假结果的星标或 Room 元数据筛选操作

### Requirement: Explicit loading, empty, denied, and error states

媒体页 SHALL 区分加载中、媒体库为空、权限未授予和查询失败四种状态，并为用户提供与状态匹配的反馈。

#### Scenario: 正在读取 MediaStore
- **WHEN** 系统媒体查询尚未完成
- **THEN** 页面显示加载状态且不显示错误或空库提示

#### Scenario: 已授权但媒体库为空
- **WHEN** 查询成功且没有可访问图片或视频
- **THEN** 页面显示媒体库为空的提示

#### Scenario: MediaStore 查询失败
- **WHEN** ContentResolver 查询抛出异常
- **THEN** 页面显示加载失败状态和重试操作

### Requirement: Read-only system media preview

点击网格项目 SHALL 打开对应系统媒体的只读预览。图片 SHALL 可查看，视频 SHALL 可播放。该入口 SHALL NOT 暴露编辑、删除、移动或上传操作。

#### Scenario: 打开图片预览
- **WHEN** 用户点击系统图片
- **THEN** 预览页通过该图片的 content URI 显示正确内容

#### Scenario: 打开视频预览
- **WHEN** 用户点击系统视频
- **THEN** 预览页通过该视频的 content URI 播放正确内容

### Requirement: Refresh after permission or lifecycle changes

媒体页 SHALL 在首次获得媒体权限后加载数据，并在页面随应用回到前台时刷新，以反映系统媒体库变化。

#### Scenario: 授权后加载
- **WHEN** 用户在权限请求中授予至少一种媒体类型访问权
- **THEN** 页面立即查询并显示该类型的可访问媒体

#### Scenario: 从系统相册返回
- **WHEN** 用户在其他应用中新增或删除媒体后返回本应用媒体页
- **THEN** 页面重新查询 MediaStore 并反映当前可访问内容
