@echo off
set DATA_ROOT=E:\AskTao\data
set UPLOAD_DIR=E:\AskTao\Uploads
set STATIC_DIRS=E:\AskTao
set HOST=0.0.0.0
set PORT=8002
set FFMPEG_PATH=C:\Users\christluck\Documents\ffmpeg\bin\ffmpeg.exe
set FFPROBE_PATH=C:\Users\christluck\Documents\ffmpeg\bin\ffprobe.exe
cd /d %~dp0


@REM uv run scripts/check_tags_consistency.py

uv run scripts/rename_tag.py 正面 正常