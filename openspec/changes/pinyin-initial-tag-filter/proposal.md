## Why

Tag 自动补全目前只支持汉字匹配，输入中文标签需要切换输入法打汉字。支持拼音首字母筛选后，用户可以直接用英文键盘输入每个字的首字母（如 `sj` 匹配「数据」），大幅提升标签输入效率。

## What Changes

- 在 tag 自动补全的匹配逻辑中增加拼音首字母匹配：对每个标签的中文字符提取拼音首字母，与用户输入进行前缀匹配
- 引入轻量拼音库（如 pinyin-pro 或预生成映射表）用于汉字→拼音首字母转换
- 匹配优先级：精确文本匹配 > 拼音首字母匹配

## Capabilities

### New Capabilities
- `pinyin-tag-match`: 为 tag 自动补全增加拼音首字母匹配能力，支持用拼音首字母筛选中文标签

### Modified Capabilities

## Impact

- `vue/src/composables/useTagAutocomplete.ts` — 修改过滤逻辑，增加拼音首字母匹配
- 新增前端依赖：拼音转换库
- 不影响后端，纯前端变更
