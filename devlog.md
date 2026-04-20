# 开发日志

## 2026-04-20

### 消息日期跳转功能

在消息流页面添加了日历弹窗日期跳转功能：

1. **可点击日期徽章**：顶部浮动日期徽章改为可点击按钮，带日历图标，点击弹出 v-calendar 日历面板
2. **消息分布标记**：日历打开时调用 `/messages/dates` 接口获取每月消息分布，有消息的日期显示紫色圆点
3. **月份按需加载**：切换月份时自动加载该月数据，已加载月份缓存到 Map 中避免重复请求
4. **日期跳转**：选择有消息的日期后，以该日期末尾作为 cursor 查询消息，清空列表重新加载，进入历史浏览模式可双向滚动
5. **深色模式**：利用 v-calendar 内置 `is-dark` 属性自动适配
6. **点击外部关闭**：document click 监听实现 popover 外部点击关闭

涉及文件：`vue/src/views/Message.vue`

## 2026-04-17

### 改进 Tag 逻辑

1. **数据迁移脚本** (`backend/migrate_tags_to_text.py`)：将 message 关联的 tag 以 `#tag` 格式 prepend 到 text 开头，使 text 成为 tag 的 source of truth。支持 `--dry-run` 预览。

2. **统一正则**：后端 hashtag 正则对齐 Android，支持连字符和 CJK 扩展 B 区：`#([\w\u4e00-\u9fff\u3400-\u4dbf-]+)`。

3. **PATCH 全量替换**：`PATCH /messages/{id}` 编辑文本时改用 `merge=False`，删掉 `#tag` 后标签会被正确移除。sync/apply 路由保持 `merge=True`。

4. **Tag CRUD 端点**：
   - `POST /tags` — 创建标签
   - `PATCH /tags/{id}` — 重命名/改分类
   - `DELETE /tags/{id}` — 删除标签及 message_tag 关联

5. **Orphan tag 清理**：`DELETE /messages/{id}` 后自动清理引用计数为 0 的 tag。

6. **前端 tag chips 智能显示**：MessageCard 底部的 tag chips 仅在文本被 `line-clamp` 折叠时显示，未折叠时隐藏，避免短文本信息重复。

### 统一三页面视觉风格

- Header 标题统一为 `text-lg font-bold`，间距统一为 `py-3`（Message 从 text-base/py-2，Media 从 text-xl，Actor 从 text-2xl/py-4）
- Media 页筛选按钮颜色从硬编码 `bg-pink-600` 改为 CSS 变量 `bg-[var(--color-primary-600)]`，loading spinner 同步
- 三页空状态统一为居中 flex + 旋转圆角卡片图标 + `text-[var(--text-primary)]` 标题 + `text-[var(--text-muted)]` 副标题

### 移除侧边栏

- **Media.vue**：移除右侧固定侧边栏（日历占位），去掉 `2xl:pr-72` padding
- **Actor.vue**：移除右侧演员详情侧边栏（头像、简介、信息、编辑/删除按钮），清理 `resolveUrl`、`formatDateTime` 未使用导入
