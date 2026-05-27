# 媒体智能查询 — 后续 TODO

## 立即要做（用户手动操作）

- [ ] 安装新依赖：`cd backend && uv pip install -e .`（onnxruntime / numpy / pillow / tokenizers）
- [ ] 跑迁移：`cd backend && alembic upgrade head` → 确认 `media_embedding` 表建好
- [ ] 准备 CLIP 模型文件放到 `{DATA_ROOT}/models/clip/`：
  - `visual.onnx`（输入 1x3x224x224 float32 → 1x512）
  - `textual.onnx`（输入 1x77 int64 → 1x512）
  - `tokenizer.json`（HuggingFace tokenizers 格式的 CLIP BPE）
  - 推荐来源：`openai/clip-vit-base-patch32` 转 onnx
- [ ] 启动 backend 后调 `GET /smart/status` → `available: true`
- [ ] 调 `POST /smart/embeddings/rebuild`（body `{}`）预热全库 embedding
- [ ] 前端 `pnpm dev`，预览页测「智能 tag」「找相似」，Media 顶栏测文本搜索

## 本期范围外（已记入开发日志）

- [ ] 视频中间帧采样（当前仅用首帧缩略图，对长视频可能漏内容）
- [ ] 引入向量索引（faiss / sqlite-vss）— 库规模超 5 万条时再考虑
- [ ] 上传管线自动 embedding（当前完全手动触发，可选加后台队列）
- [ ] 内置候选词表（如 wd14 / RAM 通用词），扩展超出现有 `Tag.name` 的覆盖
- [ ] Android 端接 smart 路由（embedding 表不进 SyncLog，Android 暂不消费）

## 可能的改进（视使用情况而定）

- [ ] `/smart/tags/suggest` 加 `prompt_template` 参数，支持 `"a photo of {name}"` 之类的提示模板提升零样本
- [ ] 建议抽屉支持手动输入自由文本 tag（新建 + 立即应用）
- [ ] 相似模式支持多种"相似维度"切换：视觉相似 / 同 actor / 同时间段
- [ ] 文本搜索结果按 score 过滤阈值（避免低相关结果）
- [ ] embedding 表加 `model` 列校验，换模型时自动失效旧 vector
- [ ] Admin 页加「重建全部 embedding」按钮（当前只能调 API）
