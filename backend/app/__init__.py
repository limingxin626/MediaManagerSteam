from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from logging.handlers import RotatingFileHandler
from app.routers import all_routers
from app.config import config

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

# 配置静态文件服务
app.mount("/uploads", StaticFiles(directory="./uploads"), name="uploads")

# 从配置动态挂载AskTao数据目录
for server_path, system_path in config.get_static_mounts().items():
    if os.path.exists(system_path):
        # 使用路径的最后一部分作为name（去掉开头的/）
        mount_name = server_path.lstrip("/").replace("/", "_") or "root"
        app.mount(server_path, StaticFiles(directory=system_path), name=mount_name)

# 注册所有路由
for router in all_routers:
    app.include_router(router)
