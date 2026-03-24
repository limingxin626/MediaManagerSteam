import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Message, Media, MessageMedia
from datetime import datetime
import shutil
from sqlalchemy import func

def backup_database():
    backup_path = 'db_new.sqlite3.backup.reorganize'
    if os.path.exists(backup_path):
        os.remove(backup_path)
    shutil.copy('db_new.sqlite3', backup_path)
    print(f"Database backed up to {backup_path}")

def contains_chinese(text):
    """Check if text contains Chinese characters"""
    if not text:
        return False
    # Unicode range for Chinese characters
    chinese_pattern = re.compile(r'[\u4e00-\u9fff]')
    return bool(chinese_pattern.search(text))

def get_filename_from_path(file_path):
    """Extract filename without extension from file path"""
    if not file_path:
        return None
    # Get basename and remove extension
    basename = os.path.basename(file_path)
    # Remove extension
    filename_without_ext = os.path.splitext(basename)[0]
    return filename_without_ext

def find_target_media(db):
    """Find all media with file_path starting with E:/AskTao/未分类/默认/"""
    target_path = 'E:/AskTao/未分类/默认/'
    media_list = db.query(Media).filter(Media.file_path.like(f'{target_path}%')).all()
    print(f"Found {len(media_list)} media items with path starting with '{target_path}'")
    return media_list

def get_message_media_relations(db, media_ids):
    """Get all MessageMedia relations for the given media IDs"""
    relations = db.query(MessageMedia).filter(MessageMedia.media_id.in_(media_ids)).all()
    print(f"Found {len(relations)} MessageMedia relations to process")
    return relations

def get_messages_to_delete(db, media_ids):
    """Find messages that only contain the target media"""
    # Get all message IDs that have relations with target media
    message_ids_with_target = db.query(MessageMedia.message_id).filter(
        MessageMedia.media_id.in_(media_ids)
    ).distinct().all()
    message_ids_with_target = [m[0] for m in message_ids_with_target]
    
    messages_to_delete = []
    for message_id in message_ids_with_target:
        # Count total media in this message
        total_media = db.query(func.count(MessageMedia.id)).filter(
            MessageMedia.message_id == message_id
        ).scalar()
        
        # Count target media in this message
        target_media_count = db.query(func.count(MessageMedia.id)).filter(
            MessageMedia.message_id == message_id,
            MessageMedia.media_id.in_(media_ids)
        ).scalar()
        
        # If all media in this message are target media, delete the message
        if total_media == target_media_count:
            message = db.query(Message).filter(Message.id == message_id).first()
            if message:
                messages_to_delete.append(message)
    
    print(f"Found {len(messages_to_delete)} messages to delete (contain only target media)")
    return messages_to_delete

def delete_existing_relations(db, media_ids):
    """Delete all MessageMedia relations for target media"""
    deleted_count = db.query(MessageMedia).filter(
        MessageMedia.media_id.in_(media_ids)
    ).delete(synchronize_session=False)
    db.commit()
    print(f"Deleted {deleted_count} existing MessageMedia relations")
    return deleted_count

def delete_orphan_messages(db, messages_to_delete):
    """Delete messages that only contained target media"""
    deleted_count = 0
    for message in messages_to_delete:
        db.delete(message)
        deleted_count += 1
    db.commit()
    print(f"Deleted {deleted_count} orphan messages")
    return deleted_count

def create_new_messages_for_media(db, media_list):
    """Create new messages for each target media"""
    created_messages = []
    
    for i, media in enumerate(media_list):
        # Get filename and check for Chinese
        filename = get_filename_from_path(media.file_path)
        text = filename if contains_chinese(filename) else None
        
        # Create new message
        new_message = Message(
            text=text,
            actor_id=None,  # Keep actor empty
            created_at=media.created_at,
            updated_at=media.created_at
        )
        db.add(new_message)
        db.flush()  # Get the ID
        
        created_messages.append((new_message, media))
        
        if (i + 1) % 100 == 0:
            print(f"Created {i + 1}/{len(media_list)} new messages")
    
    db.commit()
    print(f"Created {len(created_messages)} new messages")
    return created_messages

def create_message_media_links(db, message_media_pairs):
    """Create MessageMedia links between new messages and media"""
    created_count = 0
    
    for i, (message, media) in enumerate(message_media_pairs):
        message_media = MessageMedia(
            message_id=message.id,
            media_id=media.id,
            position=0,
            created_at=media.created_at
        )
        db.add(message_media)
        created_count += 1
        
        if (i + 1) % 100 == 0:
            print(f"Created {i + 1}/{len(message_media_pairs)} MessageMedia links")
    
    db.commit()
    print(f"Created {created_count} MessageMedia links")
    return created_count

def verify_changes(db, original_media_count):
    """Verify the changes"""
    print("\n" + "="*60)
    print("Verification Results:")
    print("="*60)
    
    # Check target media
    target_path = 'E:/AskTao/未分类/默认/'
    target_media = db.query(Media).filter(Media.file_path.like(f'{target_path}%')).all()
    print(f"\nTarget media count: {len(target_media)}")
    
    # Check that each target media has exactly one MessageMedia link
    single_link_count = 0
    no_link_count = 0
    multiple_links_count = 0
    
    for media in target_media:
        link_count = db.query(func.count(MessageMedia.id)).filter(
            MessageMedia.media_id == media.id
        ).scalar()
        
        if link_count == 1:
            single_link_count += 1
        elif link_count == 0:
            no_link_count += 1
        else:
            multiple_links_count += 1
    
    print(f"  Media with exactly 1 link: {single_link_count}")
    print(f"  Media with no links: {no_link_count}")
    print(f"  Media with multiple links: {multiple_links_count}")
    
    # Check messages with text (containing Chinese)
    messages_with_text = db.query(Message).filter(Message.text.isnot(None)).count()
    messages_without_text = db.query(Message).filter(Message.text.is_(None)).count()
    print(f"\nMessages with text (Chinese filename): {messages_with_text}")
    print(f"Messages without text: {messages_without_text}")
    
    # Check messages with empty actor
    messages_no_actor = db.query(Message).filter(Message.actor_id.is_(None)).count()
    print(f"Messages with no actor: {messages_no_actor}")
    
    # Sample some results
    print(f"\nSample results:")
    sample_messages = db.query(Message).filter(
        Message.text.isnot(None)
    ).limit(5).all()
    
    for msg in sample_messages:
        media = db.query(Media).join(MessageMedia).filter(
            MessageMedia.message_id == msg.id
        ).first()
        if media:
            print(f"  Message ID {msg.id}: '{msg.text}' -> {os.path.basename(media.file_path)}")

def main():
    print("="*60)
    print("Reorganize Uncategorized Media Script")
    print("="*60)
    
    # Backup database
    backup_database()
    
    db = SessionLocal()
    
    try:
        # Step 1: Find target media
        print("\nStep 1: Finding target media...")
        target_media = find_target_media(db)
        
        if not target_media:
            print("No target media found. Exiting.")
            return
        
        media_ids = [m.id for m in target_media]
        
        # Step 2: Find messages to delete (those that only contain target media)
        print("\nStep 2: Finding messages to delete...")
        messages_to_delete = get_messages_to_delete(db, media_ids)
        
        # Step 3: Delete existing MessageMedia relations
        print("\nStep 3: Deleting existing MessageMedia relations...")
        delete_existing_relations(db, media_ids)
        
        # Step 4: Delete orphan messages
        print("\nStep 4: Deleting orphan messages...")
        delete_orphan_messages(db, messages_to_delete)
        
        # Step 5: Create new messages for each target media
        print("\nStep 5: Creating new messages for each media...")
        message_media_pairs = create_new_messages_for_media(db, target_media)
        
        # Step 6: Create MessageMedia links
        print("\nStep 6: Creating MessageMedia links...")
        create_message_media_links(db, message_media_pairs)
        
        # Step 7: Verify changes
        print("\nStep 7: Verifying changes...")
        verify_changes(db, len(target_media))
        
        print("\n" + "="*60)
        print("Reorganization completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        print("Changes rolled back.")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
