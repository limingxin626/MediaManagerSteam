## ADDED Requirements

### Requirement: 底部输入栏替代 FAB
移除右下角 FAB 按钮，在消息流底部添加居中的假输入框作为创建消息入口。

#### Scenario: 用户点击输入栏创建消息
- **WHEN** 用户点击底部输入栏
- **THEN** 弹出 MessageComposeDialog（create 模式）

#### Scenario: 输入栏默认显示
- **WHEN** 消息页面加载完成
- **THEN** 底部显示带 placeholder 文字的输入框样式栏，居中于消息流底部

#### Scenario: 移动端不遮挡底部导航
- **WHEN** 在移动端查看消息页面
- **THEN** 输入栏位于底部导航栏上方，两者不重叠
