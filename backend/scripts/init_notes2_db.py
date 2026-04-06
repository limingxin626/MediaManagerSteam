import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 切换到 backend 目录
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')

print("初始化第二套笔记数据库...")

# 设置环境变量 DB_NAME 为 notes2
os.environ["DB_NAME"] = "notes2"

# 导入模型和引擎
from app.models import Base, engine

# 创建所有表
print("创建数据库表...")
Base.metadata.create_all(bind=engine)

print("第二套笔记数据库初始化完成！")
