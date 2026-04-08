from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from logging.handlers import RotatingFileHandler
from app.routers import all_routers
from app.config import config
from app.services.sync_log_service import register_sync_listeners

# 配置日志
log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

# 创建根日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding="utf-8"
        ),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)

# 创建FastAPI应用
app = FastAPI(
    title="媒体信息管理系统API",
    description="用于管理人员、分组、媒体资源和标签的后端接口",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置具体的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 检查挂载目录名称冲突（重复则退出）
config.check_mount_names()

# 配置静态文件服务（所有目录以文件夹名为 URL 前缀挂载）
for url_prefix, system_path in config.get_static_mounts().items():
    os.makedirs(system_path, exist_ok=True)
    mount_name = url_prefix.lstrip("/")
    app.mount(url_prefix, StaticFiles(directory=system_path), name=mount_name)

# 注册所有路由
for router in all_routers:
    app.include_router(router)

# 注册 SyncLog 事件监听器
register_sync_listeners()

# 检查 ffmpeg/ffprobe 路径
config.check_paths()
