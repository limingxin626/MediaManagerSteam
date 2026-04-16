## ADDED Requirements

### Requirement: @ 语法解析实体引用
消息文本中的 `@实体名` 语法 SHALL 被自动解析为 type=entity 的 Tag 关联，与 `#标签名` 解析为 type=tag 的逻辑并行。

#### Scenario: 消息文本包含 @ 引用
- **WHEN** 创建或更新消息，文本中包含 `@小明`
- **THEN** 系统 SHALL 查找或创建 name=小明、type=entity 的 Tag，并关联到该消息

#### Scenario: 消息文本同时包含 # 和 @
- **WHEN** 创建或更新消息，文本为 `和 @小明 @小红 去旅行 #风景 #旅行`
- **THEN** 系统 SHALL 创建/关联两个 type=entity 的 Tag（小明、小红）和两个 type=tag 的 Tag（风景、旅行）

#### Scenario: @ 引用的实体已存在
- **WHEN** 文本中 `@道德经` 且已有 name=道德经、type=entity 的 Tag
- **THEN** 系统 SHALL 复用已有记录，不创建重复

### Requirement: 解析支持中文和字母数字
`@` 和 `#` 的解析正则 SHALL 支持中文字符、英文字母和数字。

#### Scenario: 中文实体名
- **WHEN** 文本包含 `@道德经`
- **THEN** SHALL 解析出实体名 `道德经`

#### Scenario: 英文实体名
- **WHEN** 文本包含 `@JohnDoe`
- **THEN** SHALL 解析出实体名 `JohnDoe`

### Requirement: 全量替换语义同时覆盖 # 和 @
`sync_tags_from_text()` 在全量替换模式下 SHALL 同时处理 `#` 和 `@` 解析的结果，替换该消息的所有 tag 关联。

#### Scenario: 全量替换包含两种类型
- **WHEN** 消息原有标签为 [#哲学, @老子]，更新文本为 `@庄子 #道家`
- **THEN** 消息的标签 SHALL 变为 [@庄子, #道家]，移除原有的 [#哲学, @老子] 关联

#### Scenario: 合并模式保留手动标签
- **WHEN** merge=True 且消息原有标签为 [#哲学]，更新文本新增 `@庄子`
- **THEN** 消息的标签 SHALL 包含 [#哲学, @庄子]
