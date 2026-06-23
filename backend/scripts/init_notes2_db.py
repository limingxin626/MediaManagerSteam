"""在当前 DATA_ROOT 指向的库上建表(SQLAlchemy create_all)。

「第二套库」不再靠 DB_NAME(已废弃)区分 —— 现在 instance == DATA_ROOT。
要在哪套库建表,就把 DATA_ROOT 指过去再跑本脚本:

    # 方式一:临时注入(不动 .env)
    DATA_ROOT=D:/Note/notes2 python scripts/init_notes2_db.py

    # 方式二:先在 backend/.env 把 DATA_ROOT 切到目标库,再跑
    python scripts/init_notes2_db.py

注意:正式建表/迁移优先用 `alembic upgrade head`(同样跟随 DATA_ROOT);
本脚本是不带 migration 历史的快速建表,仅用于从零初始化一套空库。
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 切换到 backend 目录
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')

# 导入模型和引擎(import 时 app.config 会自动加载 backend/.env)
from app.config import config
from app.models import Base, engine

print(f"在 DATA_ROOT={config.DATA_ROOT} 的库上建表...")
print(f"  DB: {config.get_db_path()}")

# 创建所有表
Base.metadata.create_all(bind=engine)

print("建表完成！")
