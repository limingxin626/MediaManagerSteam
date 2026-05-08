# 开发日志

## 2026-05-07

### 消息编辑器升级为 Milkdown (Crepe) WYSIWYG

将 `MessageComposeDialog` 的纯 textarea 替换为 Milkdown Crepe 一体化编辑器，写作时即可看到加粗/标题/列表等渲染效果，体验接近 Notion。

1. **依赖**：新增 `@milkdown/crepe` + `@milkdown/kit` (7.20.0)
2. **新组件 `MilkdownEditor.vue`**：封装 Crepe 实例，对外暴露 `v-model:modelValue`、`focus()`、`getMarkdown()`、`getCursorCoords()`、`getTextBeforeCursor()`、`deleteBeforeCursor()`、`registerKeydown()`，便于上层做 hashtag 联想等扩展
3. **样式**：`style.css` 引入 `@milkdown/crepe/theme/common/style.css` 和 `frame.css`；为 `.dark .milkdown` 单独覆盖 `--crepe-color-*` 变量（基于 `frame-dark` 配色，主色改为项目紫 `#818cf8`），保持深色一致
4. **Hashtag 适配 `useTagAutocompleteEditor.ts`**：在 ProseMirror View 上监听 keydown，从光标前文本反向扫到 `#` 检测查询；选择标签时通过 `tr.delete` 删除 `#xxx` 段落，复用 `addTag` 把标签加入 chips
5. **共享匹配工具 `utils/tagMatch.ts`**：把原 `useTagAutocomplete` 中的 `matchTags()`/`pushRecentTag()` 抽出，新旧两个 composable 共用，避免逻辑漂移
6. **保留**：`MessageCard` 渲染（marked + prose）、后端 `#hashtag` 抽取、媒体附件流程一律不变；旧 `useTagAutocomplete.ts` 暂保留以备后续清理

涉及文件：
- 新增：`vue/src/components/MilkdownEditor.vue`、`vue/src/composables/useTagAutocompleteEditor.ts`、`vue/src/utils/tagMatch.ts`
- 修改：`vue/src/components/MessageComposeDialog.vue`、`vue/src/composables/useTagAutocomplete.ts`、`vue/src/style.css`、`vue/package.json`

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
