"""
把 DB 中 mime='image/gif' 的 media 转成 MP4 preview,给 iOS MyNote 用
AVPlayer 硬件解码播。

源:GIF 还在 uploads 目录(file_path + repo_id resolve)
输出:{DATA_ROOT}/preview/{media_id}.mp4

不动 media.file_path、不改 mime_type —— 原 GIF 仍是大图源,MP4 只是
缩略图预览的旁路文件。已有 thumb 静态 webp 也保留(无冲突)。

用法:
    cd backend
    python scripts/transcode_gif_previews.py --dry-run
    python scripts/transcode_gif_previews.py
    python scripts/transcode_gif_previews.py --limit 5      # 只跑前 5 个测试
    python scripts/transcode_gif_previews.py --force        # 覆盖已存在的 preview

ffmpeg 命令(实测必须加 :force_divisible_by=2,否则奇数维度 169x300 会崩):
    ffmpeg -i input.gif \
        -c:v libx264 -pix_fmt yuv420p \
        -vf "scale='min(300,iw)':'min(300,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2" \
        -r 10 -movflags +faststart -an -y output.mp4
"""

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

# 不走 `from app.config import config` —— 那会触发 app/__init__.py 启动,
# 它会 makedirs 所有 repository 挂载点(用户没插 /Volumes/英睿达 时崩)
# 然后 StaticFiles 还会校验目录存在,一路失败。
# 改为直接 importlib 加载 app/config.py 和 app/models/__init__.py,
# 完全绕开 app package 的初始化。

def _load_module(name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # 让后续 import 命中缓存
    spec.loader.exec_module(mod)
    return mod

# 先 mock 掉 app package,避免任何子模块的"from app import" 触发出错
import types
_app_pkg = types.ModuleType("app")
_app_pkg.__path__ = [os.path.join(BACKEND_DIR, "app")]
sys.modules["app"] = _app_pkg

config_mod = _load_module("app.config", os.path.join(BACKEND_DIR, "app", "config.py"))
config = config_mod.config

models_mod = _load_module("app.models", os.path.join(BACKEND_DIR, "app", "models", "__init__.py"))
Media = models_mod.Media
SessionLocal = models_mod.SessionLocal

FFMPEG = config.FFMPEG_PATH
PREVIEW_DIR = Path(config.get_preview_dir())


def resolve_source_abs(media: Media) -> str:
    """把 media.file_path (相对路径) 解析成 uploads 下的绝对路径。

    用 config.resolve_to_absolute 拿权威绝对路径(走 repository 挂载);
    失败时 fallback 直接拼到 default repo (uploads) 下。
    """
    try:
        return config.resolve_to_absolute(media.repo_id or "uploads", media.file_path)
    except Exception:
        # 兜底:同 config.register_relative 的逻辑
        if media.file_path.startswith("/"):
            return media.file_path
        return str(Path(config.get_upload_dir()) / media.file_path)


def transcode_one(media: Media, force: bool) -> dict:
    out_path = config.get_preview_path(media.id)
    if os.path.exists(out_path) and not force:
        return {"id": media.id, "skipped": True, "out": out_path}

    src = resolve_source_abs(media)
    if not os.path.exists(src):
        return {"id": media.id, "error": f"source not found: {src}"}

    # scale 必须 force_divisible_by=2 —— 实测 169x300 奇数维度 ffmpeg 8.x 报
    # "width not divisible by 2" 崩。min(300, iw) 同时保证短边 300 / 不放大。
    vf = ("scale='min(300,iw)':'min(300,ih)':"
          "force_original_aspect_ratio=decrease:"
          "force_divisible_by=2")
    cmd = [
        FFMPEG, "-y", "-i", src,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-vf", vf,
        "-r", "10",
        "-movflags", "+faststart",
        "-an",
        out_path,
    ]
    try:
        # 不开 text=True: 源路径含中文(未分类/默认/...),ffmpeg 在 stderr 里
        # 拼出 GBK 字节流,subprocess 默认按 utf-8 解会抛 UnicodeDecodeError。
        # 手动按系统 locale 解,失败就当 latin-1(无 decode 错误)。
        r = subprocess.run(cmd, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        return {"id": media.id, "error": "ffmpeg timeout 120s"}
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""
        last_line = err.strip().splitlines()[-3:] if err else []
        return {"id": media.id, "error": " | ".join(last_line) or "unknown"}
    return {
        "id": media.id,
        "out": out_path,
        "src_size": os.path.getsize(src),
        "out_size": os.path.getsize(out_path),
    }


def main():
    ap = argparse.ArgumentParser(description="把 DB 中 GIF media 转成 MP4 preview (iOS AVPlayer 用)")
    ap.add_argument("--dry-run", action="store_true", help="只列出待转码,不入输出文件")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的 preview")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 个(测试用)")
    args = ap.parse_args()

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    db = SessionLocal()
    try:
        gifs = db.query(Media).filter(Media.mime_type == "image/gif").order_by(Media.id).all()
        if args.limit:
            gifs = gifs[:args.limit]
        print(f"待转码 GIF: {len(gifs)}", file=sys.stderr)
        print(f"输出目录: {PREVIEW_DIR}", file=sys.stderr)
        print(f"ffmpeg: {FFMPEG}", file=sys.stderr)
        print(f"force: {args.force}, dry-run: {args.dry_run}", file=sys.stderr)
        print(file=sys.stderr)

        if args.dry_run:
            n_src_ok = 0
            n_out_exist = 0
            for m in gifs:
                out = config.get_preview_path(m.id)
                src = resolve_source_abs(m)
                src_exists = os.path.exists(src)
                out_exists = os.path.exists(out)
                if src_exists:
                    n_src_ok += 1
                if out_exists:
                    n_out_exist += 1
                print(f"  {m.id}  src={src_exists}  out_exists={out_exists}  "
                      f"{m.file_path}")
            print(file=sys.stderr)
            print(f"总: {len(gifs)}  源存在: {n_src_ok}  preview 已存在: {n_out_exist}",
                  file=sys.stderr)
            return

        ok = 0; skip = 0; err = 0
        for m in gifs:
            r = transcode_one(m, args.force)
            if r.get("skipped"):
                skip += 1
                print(f"  ⏭  {m.id}  skip(exists)", file=sys.stderr)
            elif r.get("error"):
                err += 1
                print(f"  ✗ {m.id}  {r['error']}", file=sys.stderr)
            else:
                ok += 1
                ratio = r["out_size"] / r["src_size"] * 100 if r["src_size"] else 0
                print(f"  ✓ {m.id}  {r['src_size']//1024}KB → {r['out_size']//1024}KB "
                      f"({ratio:.0f}%)", file=sys.stderr)

        print(file=sys.stderr)
        print(f"ok: {ok}  skip: {skip}  err: {err}  total: {len(gifs)}", file=sys.stderr)
        print(f"输出目录: {PREVIEW_DIR}", file=sys.stderr)
    finally:
        db.close()


if __name__ == "__main__":
    main()
