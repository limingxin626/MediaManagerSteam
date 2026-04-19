#!/usr/bin/env python3
"""
标签重命名脚本

功能：
1. 重命名指定标签
2. 更新所有消息文本中引用的旧标签名

使用方法：
python scripts/rename_tag.py <old_name> <new_name>
"""

import os
import re
import sys
from sqlalchemy.orm import Session

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import get_db, Tag, Message

def rename_tag(old_name: str, new_name: str):
    """
    重命名标签并更新消息文本中的引用
    
    Args:
        old_name: 旧标签名
        new_name: 新标签名
    """
    # 连接数据库
    db = next(get_db())
    
    try:
        # 查找旧标签
        old_tag = db.query(Tag).filter(Tag.name == old_name).first()
        if not old_tag:
            print(f"错误：标签 '{old_name}' 不存在")
            return
        
        # 检查新标签名是否已存在
        existing_tag = db.query(Tag).filter(Tag.name == new_name).first()
        if existing_tag:
            print(f"错误：标签 '{new_name}' 已存在")
            return
        
        # 重命名标签
        old_tag.name = new_name
        db.commit()
        print(f"成功：标签 '{old_name}' 已重命名为 '{new_name}'")
        
        # 更新消息文本中的标签引用
        update_message_tags(db, old_name, new_name)
        
    except Exception as e:
        print(f"错误：{str(e)}")
        db.rollback()
    finally:
        db.close()

def update_message_tags(db: Session, old_name: str, new_name: str):
    """
    更新消息文本中的标签引用
    
    Args:
        db: 数据库会话
        old_name: 旧标签名
        new_name: 新标签名
    """
    # 构建正则表达式，匹配标签格式：#标签名 或 #标签名#（如果标签名包含空格）
    if ' ' in old_name:
        # 标签名包含空格，格式为 #标签名#
        old_pattern = re.escape(f"#{old_name}#")
        new_tag = f"#{new_name}#"
    else:
        # 标签名不包含空格，格式为 #标签名
        # 使用单词边界确保只匹配完整的标签
        old_pattern = rf"#\b{re.escape(old_name)}\b"
        new_tag = f"#{new_name}"
    
    # 查找包含旧标签的消息
    messages = db.query(Message).filter(Message.text.ilike(f"%#{old_name}%")).all()
    
    updated_count = 0
    for message in messages:
        if message.text:
            # 替换文本中的旧标签为新标签
            updated_text = re.sub(old_pattern, new_tag, message.text)
            if updated_text != message.text:
                message.text = updated_text
                updated_count += 1
    
    if updated_count > 0:
        db.commit()
        print(f"成功：更新了 {updated_count} 条消息中的标签引用")
    else:
        print("提示：没有消息包含该标签的引用")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("使用方法：python scripts/rename_tag.py <old_name> <new_name>")
        sys.exit(1)
    
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    
    if not old_name or not new_name:
        print("错误：旧标签名和新标签名都不能为空")
        sys.exit(1)
    
    rename_tag(old_name, new_name)