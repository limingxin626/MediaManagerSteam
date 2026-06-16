@echo off
set DATA_ROOT=E:\Note\data
@REM Repository 挂载点已迁移到 %DATA_ROOT%\repositories.json,不再用 UPLOAD_DIR / STATIC_DIRS
set HOST=0.0.0.0
set PORT=8002
set FFMPEG_PATH=C:\Users\christluck\Documents\ffmpeg\bin\ffmpeg.exe
set FFPROBE_PATH=C:\Users\christluck\Documents\ffmpeg\bin\ffprobe.exe
cd /d %~dp0

if not exist "%DATA_ROOT%\db.sqlite3" (
    echo 数据库不存在，正在初始化...
    uv run alembic upgrade head
)
@REM uv run alembic upgrade head
if not exist "%DATA_ROOT%\repositories.json" (
    echo ❌ DATA_ROOT 未初始化 (%DATA_ROOT%\repositories.json 不存在)
    echo    请先运行: uv run scripts/init_data_root.py
    exit /b 1
)
uv run api.py
