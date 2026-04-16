## Why

当前"添加消息"按钮是右下角的 FAB（浮动操作按钮），位置不够显眼且不方便单手操作。将其替换为底部居中的输入框样式入口，更符合即时通讯类应用的交互习惯，提升发消息的便捷性。

## What Changes

- 移除 Message.vue 中右下角的 FAB 按钮
- 在消息流底部添加一个居中的"假输入框"（点击触发，不在框内直接输入）
- 点击假输入框后弹出现有的 `MessageComposeDialog` 组件
- 移动端底部导航栏需要为新输入栏留出空间，避免重叠

## Capabilities

### New Capabilities
- `bottom-input-bar`: 底部居中输入栏组件，替代 FAB 按钮作为创建消息的入口

### Modified Capabilities

## Impact

- `vue/src/views/Message.vue` — 移除 FAB，添加底部输入栏
- `vue/src/components/BottomNavBar.vue` — 可能需要调整布局避免与输入栏重叠
