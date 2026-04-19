import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, Message, Tag

def migrate_tags_to_text():
    """将所有 Message 的 tags 以 # 形式 prepend 到 text 中"""
    db = SessionLocal()
    try:
        # 获取所有 Message 记录
        messages = db.query(Message).all()
        total = len(messages)
        updated = 0
        
        print(f"开始迁移，共 {total} 条消息")
        
        for i, message in enumerate(messages, 1):
            # 获取消息的所有 tags
            tags = message.tags
            if not tags:
                continue
            
            # 提取 tag 名称
            tag_names = [tag.name for tag in tags]
            
            # 检查 text 是否已经包含这些 tags
            current_text = message.text or ""
            existing_tags = set()
            
            # 提取当前 text 中已有的 #tag
            for word in current_text.split():
                if word.startswith('#') and len(word) > 1:
                    existing_tags.add(word[1:])
            
            # 找出需要添加的 tags
            tags_to_add = [tag for tag in tag_names if tag not in existing_tags]
            
            if tags_to_add:
                # 构建 tag 字符串
                tag_string = ' '.join([f'#{tag}' for tag in tags_to_add])
                
                # 检查 text 是否为空
                if not current_text:
                    # 如果 text 为空，直接使用标签字符串
                    new_text = tag_string
                else:
                    # 检查 text 是否以标签开头
                    text_starts_with_tag = False
                    first_word = current_text.split()[0] if current_text.strip() else ''
                    if first_word.startswith('#') and len(first_word) > 1:
                        text_starts_with_tag = True
                    
                    # 根据情况添加分隔符
                    if text_starts_with_tag:
                        # 如果 text 以标签开头，添加空格
                        new_text = f"{tag_string} {current_text}"
                    else:
                        # 否则添加换行
                        new_text = f"{tag_string}\n{current_text}"
                
                # 更新 message.text
                message.text = new_text
                updated += 1
                
                if i % 100 == 0:
                    print(f"处理进度: {i}/{total}, 已更新: {updated}")
        
        # 提交事务
        db.commit()
        print(f"迁移完成，共更新 {updated} 条消息")
        
    except Exception as e:
        print(f"迁移过程中出错: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_tags_to_text()
