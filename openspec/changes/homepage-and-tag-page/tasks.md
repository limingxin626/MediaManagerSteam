## 1. 导航路由调整

- [ ] 1.1 修改 `BottomNavDestination` 枚举：移除 HOME/MESSAGES/SYSTEM_GALLERY，改为 MESSAGES（主页，route 指向无过滤消息列表）、TAGS、ACTORS、MEDIA 四个 tab
- [ ] 1.2 修改 `MainActivity.kt` 中的底部导航栏配置：更新 tab 图标、标签文字、顺序（消息→标签→演员→媒体）
- [ ] 1.3 修改 NavGraph 中的 `startDestination` 为消息列表路由

## 2. 标签列表页

- [ ] 2.1 将现有 HomeScreen 重命名/改造为 TagListScreen，保留 GroupItem 分组展示逻辑
- [ ] 2.2 确保 TagListScreen 在 NavGraph 中注册到 `Routes.TAG_LIST` 路由
- [ ] 2.3 将 HomeViewModel 重命名为 TagListViewModel（或直接复用）

## 3. 设置入口迁移

- [ ] 3.1 在 MessageListScreen 顶栏添加齿轮图标，点击导航到设置页
- [ ] 3.2 从底部导航栏移除设置 tab

## 4. 清理

- [ ] 4.1 移除不再使用的 HomeScreen 相关代码（如果已完全迁移到 TagListScreen）
- [ ] 4.2 更新导航动画中与旧 tab 顺序相关的方向判断逻辑
