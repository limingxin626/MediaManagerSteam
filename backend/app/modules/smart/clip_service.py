"""CLIP onnx 推理服务。

模型文件约定放在 `{DATA_ROOT}/models/clip/`：
  - visual.onnx   — 图像编码器（输入 1x3x224x224 float32，输出 1x512）
  - textual.onnx  — 文本编码器（输入 1xN int64，输出 1x512）
  - tokenizer.json — HuggingFace tokenizers 的 BPE 模型

任何文件缺失/加载失败 → CLIPUnavailable 异常，由路由层翻成 503。
"""
from __future__ import annotations

import logging
import os
import threading
from functools import lru_cache
from typing import Optional

import numpy as np

from app.config import config

logger = logging.getLogger(__name__)


MODEL_NAME = "clip-vit-b32"
EMBED_DIM = 512
CONTEXT_LENGTH = 77  # CLIP 文本最大长度


class CLIPUnavailable(RuntimeError):
    """CLIP 模型不可用（文件缺失或加载失败）。"""


_lock = threading.Lock()
_visual_session = None
_textual_session = None
_tokenizer = None
_init_error: Optional[str] = None


def _model_dir() -> str:
    return os.path.join(config.DATA_ROOT, "models", "clip")


def _try_init() -> None:
    """懒加载 onnx session + tokenizer。失败时记录 _init_error。"""
    global _visual_session, _textual_session, _tokenizer, _init_error
    if _visual_session is not None and _textual_session is not None and _tokenizer is not None:
        return
    with _lock:
        if _visual_session is not None and _textual_session is not None and _tokenizer is not None:
            return
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as e:
            _init_error = f"依赖未安装: {e}"
            logger.error("CLIP 依赖缺失: %s", e)
            return

        mdir = _model_dir()
        visual_path = os.path.join(mdir, "visual.onnx")
        textual_path = os.path.join(mdir, "textual.onnx")
        tok_path = os.path.join(mdir, "tokenizer.json")

        for p in (visual_path, textual_path, tok_path):
            if not os.path.isfile(p):
                _init_error = f"模型文件缺失: {p}"
                logger.error(_init_error)
                return

        try:
            providers = ["CPUExecutionProvider"]
            _visual_session = ort.InferenceSession(visual_path, providers=providers)
            _textual_session = ort.InferenceSession(textual_path, providers=providers)
            _tokenizer = Tokenizer.from_file(tok_path)
            logger.info("CLIP 模型加载完成: %s", mdir)
        except Exception as e:
            _init_error = f"模型加载失败: {e}"
            logger.exception("CLIP 模型加载失败")
            _visual_session = None
            _textual_session = None
            _tokenizer = None


def is_available() -> bool:
    _try_init()
    return _visual_session is not None and _textual_session is not None and _tokenizer is not None


def get_unavailable_reason() -> str:
    _try_init()
    return _init_error or "CLIP 模型未初始化"


def _ensure() -> None:
    if not is_available():
        raise CLIPUnavailable(get_unavailable_reason())


# OpenAI CLIP 归一化常数
_IMG_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32).reshape(3, 1, 1)
_IMG_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32).reshape(3, 1, 1)


def _preprocess_image(path: str) -> np.ndarray:
    """读取图片 → 224×224 center crop → 归一化 → CHW float32 batch=1。"""
    from PIL import Image

    with Image.open(path) as img:
        img = img.convert("RGB")
        # CLIP 标准预处理：短边缩到 224，再 center crop
        w, h = img.size
        scale = 224 / min(w, h)
        new_w, new_h = int(round(w * scale)), int(round(h * scale))
        img = img.resize((new_w, new_h), Image.BICUBIC)
        left = (new_w - 224) // 2
        top = (new_h - 224) // 2
        img = img.crop((left, top, left + 224, top + 224))
        arr = np.asarray(img, dtype=np.float32) / 255.0  # HWC
    arr = arr.transpose(2, 0, 1)  # CHW
    arr = (arr - _IMG_MEAN) / _IMG_STD
    return arr[np.newaxis, ...].astype(np.float32)


def _tokenize(text: str) -> np.ndarray:
    assert _tokenizer is not None
    encoded = _tokenizer.encode(text)
    ids = encoded.ids
    # CLIP 期望 [SOT] ... [EOT]，HuggingFace 的 clip tokenizer.json 通常已包含
    if len(ids) > CONTEXT_LENGTH:
        ids = ids[:CONTEXT_LENGTH - 1] + [ids[-1]]
    padded = ids + [0] * (CONTEXT_LENGTH - len(ids))
    return np.asarray([padded], dtype=np.int64)


def encode_image(path: str) -> np.ndarray:
    """返回 L2 归一化的 (512,) float32 向量。"""
    _ensure()
    x = _preprocess_image(path)
    assert _visual_session is not None
    input_name = _visual_session.get_inputs()[0].name
    out = _visual_session.run(None, {input_name: x})[0]
    vec = out[0].astype(np.float32)
    n = float(np.linalg.norm(vec))
    return vec / n if n > 0 else vec


@lru_cache(maxsize=2048)
def encode_text(text: str) -> np.ndarray:
    """文本 embedding。LRU 缓存（按 text 字符串），返回 L2 归一化的 (512,)。"""
    _ensure()
    tokens = _tokenize(text)
    assert _textual_session is not None
    input_name = _textual_session.get_inputs()[0].name
    out = _textual_session.run(None, {input_name: tokens})[0]
    vec = out[0].astype(np.float32)
    n = float(np.linalg.norm(vec))
    return vec / n if n > 0 else vec


def vector_to_bytes(vec: np.ndarray) -> bytes:
    """float32 → float16 bytes，节省一半空间且对相似度排序无影响。"""
    return vec.astype(np.float16).tobytes()


def bytes_to_vector(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.float16).astype(np.float32)
