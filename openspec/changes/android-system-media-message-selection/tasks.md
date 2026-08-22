## 1. Media 来源模型

- [ ] 1.1 为 Room `Media` 增加 sourceType、contentUri 和 originalFileName，并提升数据库版本
- [ ] 1.2 更新远端同步、下载和本地创建映射，为已有媒体设置正确默认来源
- [ ] 1.3 增加媒体来源解析逻辑，优先可访问本地来源并回退远端 URL
- [ ] 1.4 添加 Media 来源、hash 复用和远端回退单元测试

## 2. Content URI 读取与上传

- [ ] 2.1 新增可从 File 或 ContentResolver InputStream 流式写入的上传 RequestBody
- [ ] 2.2 将首次发送上传改为统一使用媒体来源读取，不要求私有文件路径
- [ ] 2.3 将 retrySync 上传改为支持保存的 MediaStore content URI
- [ ] 2.4 对 URI 不可访问、权限失效和读取中断返回明确失败，禁止上传空文件
- [ ] 2.5 添加 content URI 上传、重新打开流和失败分类测试

## 3. 系统媒体 Message 创建

- [ ] 3.1 为 `MessageViewModel` 增加接收有序 `List<SystemMedia>` 的单 Message 创建入口
- [ ] 3.2 在 IO dispatcher 计算 hash 并直接构造 MEDIA_STORE Media，不复制文件或生成私有缩略图
- [ ] 3.3 复用 `createMessageWithMedia` 单事务落库和现有 create-from-client 同步流程
- [ ] 3.4 保证网络异常进入 PENDING_SYNC、源文件异常进入 PUSH_FAILED，且重试可恢复
- [ ] 3.5 添加多媒体单 Message、position 顺序、去重和发送状态测试

## 4. 展示来源兼容

- [ ] 4.1 更新 Message 缩略图组件以加载 content URI 并在失败时回退 remoteThumbnailUrl
- [ ] 4.2 更新共享图片预览以加载 content URI 并回退 remoteMediaUrl
- [ ] 4.3 更新视频播放器以播放 content URI 并回退远端 URL
- [ ] 4.4 为无本地或远端来源的媒体增加“原始媒体不可用”状态

## 5. Media 网格多选

- [ ] 5.1 在 MediaViewModel 或页面状态中增加选择模式、stableKey 集合、提交状态和清理逻辑
- [ ] 5.2 为 SystemMediaCard 接入区分普通点击、长按和选中视觉状态的手势
- [ ] 5.3 在 LazyVerticalGrid 层实现基于 visibleItemsInfo 命中的跨项目滑动添加/移除
- [ ] 5.4 保证每次拖动中每个项目只处理一次，并处理与网格滚动的手势协调
- [ ] 5.5 筛选或 MediaStore 刷新后移除不可见/不存在的选择
- [ ] 5.6 添加选择 reducer/手势命中纯逻辑测试

## 6. 浮动创建操作

- [ ] 6.1 在选择模式底部显示选中数量、“创建”和“取消”的浮动 Surface
- [ ] 6.2 创建按钮按当前网格顺序收集媒体并调用系统媒体 Message 创建入口
- [ ] 6.3 提交期间禁用重复创建；本地创建开始后退出并清空选择
- [ ] 6.4 调整网格 content padding 和底部导航间距，避免浮动栏遮挡内容

## 7. 验证

- [ ] 7.1 运行 Android unit tests、lint 和 assembleDebug
- [ ] 7.2 真机验证长按、点击切换、快速滑动选择、拖动移除和边缘滚动
- [ ] 7.3 真机验证多个图片/视频组成一条 Message，且应用私有目录无媒体副本
- [ ] 7.4 验证离线创建、恢复网络重试、撤销媒体权限和删除原文件
- [ ] 7.5 验证已同步媒体删除原文件后可回退远端预览
- [ ] 7.6 验证创建 Message 不继承或改变 system media 收藏与标签
