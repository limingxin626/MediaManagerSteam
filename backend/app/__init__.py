from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import sys
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
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="媒体信息管理系统API",
    description="用于管理人员、分组、媒体资源和标签的后端接口",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 校验 repositories.json 的 repo_id 与内置 /data 前缀不冲突
config.validate_repositories()

# 校验 DATA_ROOT 必须存在(不自动创建,运行 init 脚本来建)
data_root = config.DATA_ROOT
if not os.path.isdir(data_root):
    logger.critical(
        "DATA_ROOT=%s 不存在。请运行 `uv run scripts/init_data_root.py` 初始化。",
        data_root,
    )
    sys.exit(1)

# 配置静态文件服务:每个挂载点单独检查,缺失就跳过(允许外接盘未挂)
mounted = 0
skipped = 0
for url_prefix, system_path in config.get_static_mounts().items():
    if not os.path.isdir(system_path):
        logger.warning(
            "[static] %s → %s 不存在,跳过挂载(对应 media URL 将返回 404)",
            url_prefix, system_path,
        )
        skipped += 1
        continue
    mount_name = url_prefix.lstrip("/")
    app.mount(url_prefix, StaticFiles(directory=system_path), name=mount_name)
    mounted += 1
logger.info("[static] 已挂载 %d 个,跳过 %d 个", mounted, skipped)

# 注册所有路由
for router in all_routers:
    app.include_router(router)

# 注册 SyncLog 事件监听器
register_sync_listeners()

# 检查 ffmpeg/ffprobe 路径
config.check_paths()

# 启动磁盘扫描后台 worker(逐个补 fs_entry 的 metadata + 缩略图)
from app.services.scan_worker import start_worker
start_worker()
