#!/bin/bash

set -e

# 目录与路径（按你的实际路径修改）
export DATA_ROOT="$HOME/data/Media/"
export HOST="0.0.0.0"
export PORT="8002"

# ffmpeg / ffprobe 路径（确保已安装，可用 which ffmpeg 查看）
export FFMPEG_PATH="/opt/homebrew/bin/ffmpeg"
export FFPROBE_PATH="/opt/homebrew/bin/ffprobe"


# # 判断数据库是否存在
# if [ ! -f "$DATA_ROOT/db.sqlite3" ]; then
#     echo "⚠️  数据库不存在，正在初始化..."
#     uv run alembic upgrade head
# else
#     echo "✓ 数据库存在，运行迁移..."
#     uv run alembic upgrade head
# fi


# uv run alembic upgrade head
if [ ! -f "$DATA_ROOT/repositories.json" ]; then
    echo "❌ DATA_ROOT 未初始化 ($DATA_ROOT/repositories.json 不存在)"
    echo "   请先运行: uv run scripts/init_data_root.py"
    exit 1
fi
uv run api.py