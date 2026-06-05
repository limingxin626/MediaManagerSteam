#!/bin/bash

# 目录与路径（按你的实际路径修改）
export DATA_ROOT="$HOME/data/Note/data"
# Repository 挂载点已迁移到 $DATA_ROOT/repositories.json,不再用 UPLOAD_DIR / STATIC_DIRS
export HOST="0.0.0.0"
export PORT="8002"

# ffmpeg / ffprobe 路径（确保已安装，可用 which ffmpeg 查看）
export FFMPEG_PATH="/opt/homebrew/bin/ffmpeg"
export FFPROBE_PATH="/opt/homebrew/bin/ffprobe"

# 切换到脚本所在目录
cd "$(dirname "$0")" || exit 1

# 判断数据库是否存在
if [ ! -f "$DATA_ROOT/db.sqlite3" ]; then
    echo "数据库不存在，正在初始化..."
    uv run alembic upgrade head
fi

# uv run alembic upgrade head

# 启动服务
uv run api.py
