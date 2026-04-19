import sys
import os
import re

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Message

def check_tags_consistency(message):
    """检查 message 的 tags 与 text 中解析出的标签是否一致。

    返回值：
    {
        'consistent': bool,  # 是否一致
        'message_tags': list,  # message.tags 中的标签名称
        'text_tags': list,     # text 中解析出的标签名称
        'missing_in_text': list,  # 在 message.tags 中但不在 text 中的标签
        'extra_in_text': list     # 在 text 中但不在 message.tags 中的标签
    }
    """
    # 获取 message.tags 中的标签名称
    message_tag_names = {tag.name for tag in message.tags}
    
    # 从 text 中解析标签（支持包含斜杠 /）
    text_tag_names = set(re.findall(r'#([\w\u4e00-\u9fff/]+)', message.text or ""))
    
    # 计算差异
    missing_in_text = list(message_tag_names - text_tag_names)
    extra_in_text = list(text_tag_names - message_tag_names)
    
    # 检查是否一致
    consistent = len(missing_in_text) == 0 and len(extra_in_text) == 0
    
    return {
        'consistent': consistent,
        'message_tags': sorted(message_tag_names),
        'text_tags': sorted(text_tag_names),
        'missing_in_text': sorted(missing_in_text),
        'extra_in_text': sorted(extra_in_text)
    }

def check_all_messages_tags():
    """检查所有消息的标签一致性"""
    db = SessionLocal()
    try:
        # 获取所有 Message 记录
        messages = db.query(Message).all()
        total = len(messages)
        consistent_count = 0
        inconsistent_count = 0
        
        print(f"开始检查标签一致性，共 {total} 条消息")
        
        # 用于存储不一致的消息
        inconsistent_messages = []
        
        for i, message in enumerate(messages, 1):
            # 检查标签一致性
            result = check_tags_consistency(message)
            
            if result['consistent']:
                consistent_count += 1
            else:
                inconsistent_count += 1
                inconsistent_messages.append({
                    'id': message.id,
                    'message_tags': result['message_tags'],
                    'text_tags': result['text_tags'],
                    'missing_in_text': result['missing_in_text'],
                    'extra_in_text': result['extra_in_text']
                })
            
            if i % 100 == 0:
                print(f"检查进度: {i}/{total}, 一致: {consistent_count}, 不一致: {inconsistent_count}")
        
        # 输出检查结果
        print(f"\n检查完成:")
        print(f"总消息数: {total}")
        print(f"标签一致: {consistent_count}")
        print(f"标签不一致: {inconsistent_count}")
        
        # 输出不一致的消息详情
        if inconsistent_messages:
            print(f"\n不一致的消息详情:")
            for msg in inconsistent_messages[:10]:  # 只显示前10条
                print(f"消息 ID: {msg['id']}")
                print(f"  消息标签: {msg['message_tags']}")
                print(f"  文本标签: {msg['text_tags']}")
                if msg['missing_in_text']:
                    print(f"  标签缺失: {msg['missing_in_text']}")
                if msg['extra_in_text']:
                    print(f"  文本多余: {msg['extra_in_text']}")
                print()
            
            if len(inconsistent_messages) > 10:
                print(f"... 还有 {len(inconsistent_messages) - 10} 条不一致的消息")
        
    except Exception as e:
        print(f"检查过程中出错: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_all_messages_tags()
