@echo off
set DATA_ROOT=C:/Users/jieli4/Documents/note/Data
set UPLOAD_DIR=C:/Users/jieli4/Documents/note/Uploads
set STATIC_DIRS=C:/Users/jieli4/Documents/note
set PORT=8002
set FFMPEG_PATH=ffmpeg
set FFPROBE_PATH=ffprobe
cd /d %~dp0
python api.py
