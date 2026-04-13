@echo off
set DATA_ROOT=./Data
set UPLOAD_DIR=./Uploads
set STATIC_DIRS=./Static
set PORT=9002
set FFMPEG_PATH=C:\Users\jieli4\Documents\ffmpeg\bin\ffmpeg
set FFPROBE_PATH=C:\Users\jieli4\Documents\ffmpeg\bin\ffprobe
cd /d %~dp0

if not exist "%DATA_ROOT%\db.sqlite3" (
    echo 数据库不存在，正在初始化...
    uv run alembic upgrade head
)

uv run api.py
