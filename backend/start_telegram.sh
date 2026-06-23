#!/bin/bash
# Telegram "Saved Messages" → backend 同步 watcher。
#
# 用法:
#   ./start_telegram.sh                   # 默认 watch 模式(长驻)
#   ./start_telegram.sh once              # 单轮增量
#   ./start_telegram.sh backfill          # 全量拉取
#   ./start_telegram.sh bootstrap         # 首次交互登录
#
# 与 start.sh 一样:fail-fast 检查 env vars,只换最后一行。
# 第一次跑前先做 bootstrap 登录,然后 backfill;之后 watch 即可。

set -e

export DATA_ROOT="${DATA_ROOT:-$HOME/data/Media/}"
export HOST="0.0.0.0"
export PORT="8002"

export FFMPEG_PATH="${FFMPEG_PATH:-/opt/homebrew/bin/ffmpeg}"
export FFPROBE_PATH="${FFPROBE_PATH:-/opt/homebrew/bin/ffprobe}"

# Telegram 必填项
: "${TELEGRAM_API_ID:?TELEGRAM_API_ID 未设置。请 export TELEGRAM_API_ID=<my.telegram.org 申请的 id>}"
: "${TELEGRAM_API_HASH:?TELEGRAM_API_HASH 未设置。请 export TELEGRAM_API_HASH=<my.telegram.org 申请的 hash>}"

# 可选项(有默认值)
export TELEGRAM_SESSION_PATH="${TELEGRAM_SESSION_PATH:-$DATA_ROOT/.telegram.session}"
export TELEGRAM_INBOX_DIR="${TELEGRAM_INBOX_DIR:-$DATA_ROOT/telegram_inbox}"
export TELEGRAM_POLL_INTERVAL="${TELEGRAM_POLL_INTERVAL:-60}"
# 单文件 ≥ 此字节数 → 只下载封面
export TELEGRAM_LARGE_FILE_THRESHOLD="${TELEGRAM_LARGE_FILE_THRESHOLD:-52428800}"

if [ ! -f "$DATA_ROOT/repositories.json" ]; then
    echo "❌ DATA_ROOT 未初始化 ($DATA_ROOT/repositories.json 不存在)"
    echo "   请先运行: uv run scripts/init_data_root.py"
    exit 1
fi

CMD="${1:-watch}"
cd "$(dirname "$0")"
uv run scripts/telegram_sync.py "$CMD"