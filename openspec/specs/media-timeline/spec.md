# media-timeline Specification

## Purpose

定义 Media 页面右侧时间轴组件的视觉、交互与滚动行为规范，提供 Apple Photos 风格的纵向日期定位体验。

## Requirements

### Requirement: 时间轴作为唯一纵向定位控件
Media 页面的浏览模式（非 Smart 搜索模式）SHALL 隐藏原生浏览器滚动条，并由右侧时间轴组件作为唯一的可视滚动 / 跳转入口。滚动能力 MUST 保留（鼠标滚轮、触控板、键盘 Page Up/Down、触屏滑动均正常工作）。

#### Scenario: 桌面端不显示滚动条
- **WHEN** 用户在桌面浏览器打开 `/media` 页面、且未触发 Smart 搜索
- **THEN** 主滚动容器的右侧不渲染任何浏览器原生滚动条（无论 Chromium / WebKit / Firefox）
- **AND** 用户仍可使用鼠标滚轮上下滚动媒体网格

#### Scenario: Smart 搜索模式无时间轴
- **WHEN** 用户进入搜索 / 相似度结果模式（`smartActive === true`）
- **THEN** 时间轴组件 MUST 不渲染，原生滚动条行为不在该模式下被本规范约束

### Requirement: Apple Photos 风格的常驻视觉
时间轴 SHALL 在桌面端以约 40px、移动端以约 28px 的常驻宽度渲染，并显示：中央细线轴、月份小刻度、年份长刻度、年份文字标签，以及当前位置指示器。视觉风格遵循 Apple Photos 的右侧索引条审美：克制、信息密度适中、与中性石墨暗色主题协调。

#### Scenario: 常驻显示年份与月份刻度
- **WHEN** 时间轴的 `timeline` 数据已加载
- **THEN** 在不悬浮、不拖动的状态下，用户也能看到所有年份的长刻度 + 年份数字 + 每月的短刻度

#### Scenario: 年份标签防重叠
- **WHEN** 时间范围内相邻两个年份标签的 `top` 百分比差小于 8%
- **THEN** 仅保留较新一年的文字标签；两年的刻度本身仍然全部渲染

#### Scenario: 暗色主题适配
- **WHEN** `<html>` 上存在 `.dark` 类
- **THEN** 时间轴的轴线、刻度、文字、指示器颜色 MUST 使用项目暗色变量（中性石墨调色板），且对比度足够辨识

### Requirement: 当前位置指示器
时间轴 SHALL 在当前滚动位置对应的日期处渲染一个圆点指示器，并由该圆点向左引出一条短线，连接到一个浮动的"YYYY年M月"胶囊标签（移动端 <640px 屏宽时胶囊可隐藏）。指示器随主容器滚动平滑过渡。

#### Scenario: 滚动时指示器跟随
- **WHEN** 用户滚动主媒体网格，导致 `currentDate` 改变
- **THEN** 圆点 + 胶囊标签的纵向位置 MUST 在 200ms 内平滑过渡到新位置
- **AND** 胶囊标签文字 MUST 反映新的"YYYY年M月"

#### Scenario: 数据稀疏时隐藏胶囊
- **WHEN** `timeline` 数据少于 2 条
- **THEN** 胶囊标签不渲染；圆点指示器仍渲染

#### Scenario: 尊重 reduce-motion
- **WHEN** 用户系统设置 `prefers-reduced-motion: reduce`
- **THEN** 指示器位置变更 MUST 立即生效，无 transition

### Requirement: 拖动跳转与毛玻璃日期气泡
用户 SHALL 能通过在时间轴上按下鼠标 / 触摸并纵向拖动，预览并跳转到任意日期。拖动过程中显示一个毛玻璃质感（`backdrop-blur`）的日期气泡，文字为"YYYY年M月D日"。

#### Scenario: 拖动预览
- **WHEN** 用户在时间轴上按下并拖动
- **THEN** 气泡跟随指针纵向位置显示当前指向的具体日期
- **AND** 媒体网格随之滚动到该日期（`@jump` 事件每帧最多触发一次，使用 rAF 节流）

#### Scenario: 释放后落定
- **WHEN** 用户松开鼠标或离开触屏
- **THEN** 组件 MUST 触发一次 `@jump-final`，承载最后一次指针位置对应的日期
- **AND** 气泡淡出消失

### Requirement: 滚轮事件转发到主滚动容器
当鼠标停在时间轴上滚动滚轮时，时间轴组件 SHALL 把该滚轮事件等效地转发到 Media 页面的主滚动容器，使列表照常滚动 —— 用户不会因为光标停在右侧"卡死"在原地。

#### Scenario: 桌面滚轮转发
- **WHEN** 鼠标位于时间轴区域，用户向上 / 向下转动滚轮
- **THEN** 主媒体滚动容器 MUST 按 `deltaY` 同方向滚动相同距离
- **AND** 浏览器默认行为不被 `preventDefault` 阻断（不破坏嵌套滚动语义）

#### Scenario: 触屏不受影响
- **WHEN** 用户在时间轴上使用触屏拖动
- **THEN** 行为仍走"按下 + 拖动跳转"路径，不被滚轮转发逻辑干扰
