## ADDED Requirements

### Requirement: 编辑消息时添加媒体文件
用户在编辑已有消息时，SHALL能够选择新的图片或视频文件添加到该消息。新媒体SHALL追加到已有媒体列表末尾，position自动递增。

#### Scenario: 添加单个文件
- **WHEN** 用户在编辑对话框中点击添加文件按钮并选择一个图片文件
- **THEN** 文件上传到服务器，创建Media记录和MessageMedia关联，媒体出现在列表末尾

#### Scenario: 添加多个文件
- **WHEN** 用户选择多个文件
- **THEN** 所有文件依次上传处理，按选择顺序追加到媒体列表末尾

#### Scenario: 添加重复文件
- **WHEN** 用户添加的文件hash与已有Media记录相同
- **THEN** 复用已有Media记录，仅创建新的MessageMedia关联

### Requirement: 编辑消息时删除媒体
用户在编辑消息时SHALL能够删除消息中的某个媒体。删除操作SHALL仅移除MessageMedia关联，不删除Media文件本身。

#### Scenario: 删除一个媒体
- **WHEN** 用户点击某个媒体缩略图上的删除按钮
- **THEN** 该媒体从消息中移除，剩余媒体position自动重排

#### Scenario: 删除后剩余媒体排序
- **WHEN** 消息有媒体A(0)、B(1)、C(2)，用户删除B
- **THEN** 媒体顺序变为A(0)、C(1)

### Requirement: 编辑消息时调整媒体顺序
用户SHALL能够通过拖拽来调整消息中媒体的显示顺序。

#### Scenario: 拖拽排序
- **WHEN** 用户将位置2的媒体拖到位置0
- **THEN** 系统调用PATCH接口的media_order参数更新顺序，所有媒体position重新计算

### Requirement: 编辑对话框展示已有媒体
编辑模式的对话框SHALL展示消息当前所有媒体的缩略图网格。

#### Scenario: 打开编辑对话框
- **WHEN** 用户点击编辑按钮打开编辑对话框
- **THEN** 对话框中展示该消息所有已有媒体的缩略图，以及添加新文件的入口

#### Scenario: 区分已有媒体和新添加文件
- **WHEN** 对话框中同时存在已有媒体和新选择的待上传文件
- **THEN** 已有媒体显示服务器缩略图，新文件显示本地预览
