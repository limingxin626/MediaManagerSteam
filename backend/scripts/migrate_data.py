import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Actor as OldActor, Media as OldMedia, Group as OldGroup
from app.models.new_models import NewSessionLocal, Message, Actor as NewActor, Media as NewMedia, MessageMedia as NewMessageMedia
from datetime import datetime
import mimetypes

def get_mime_type(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def migrate_actors(old_db, new_db):
    print("Migrating actors...")
    old_actors = old_db.query(OldActor).all()
    
    for old_actor in old_actors:
        new_actor = NewActor(
            id=old_actor.id,
            name=old_actor.name,
            description=old_actor.description,
            avatar_path=old_actor.avatar_path,
            created_at=old_actor.created_at,
            updated_at=old_actor.updated_at
        )
        new_db.add(new_actor)
    
    new_db.commit()
    print(f"Migrated {len(old_actors)} actors")

def migrate_media(old_db, new_db):
    print("Migrating media...")
    old_media_list = old_db.query(OldMedia).all()
    
    seen_hashes = set()
    skipped_count = 0
    migrated_count = 0
    
    for old_media in old_media_list:
        if old_media.file_hash and old_media.file_hash in seen_hashes:
            skipped_count += 1
            continue
        
        if old_media.file_hash:
            seen_hashes.add(old_media.file_hash)
        
        mime_type = get_mime_type(old_media.local_media_path)
        
        new_media = NewMedia(
            id=old_media.id,
            file_path=old_media.local_media_path,
            file_hash=old_media.file_hash,
            file_size=old_media.file_size,
            mime_type=mime_type,
            width=old_media.width,
            height=old_media.height,
            duration=old_media.duration,
            rating=old_media.rating or 0,
            view_count=old_media.view_count or 0,
            last_viewed_at=old_media.last_viewed_at,
            created_at=old_media.created_at,
            updated_at=old_media.updated_at
        )
        new_db.add(new_media)
        migrated_count += 1
    
    new_db.commit()
    print(f"Migrated {migrated_count} media items")
    print(f"Skipped {skipped_count} duplicate media items")

def migrate_messages_and_relations(old_db, new_db):
    print("Migrating messages and message-media relations...")
    
    old_groups = old_db.query(OldGroup).all()
    message_count = 0
    relation_count = 0
    
    for old_group in old_groups:
        # Combine group name and description with a newline
        text_parts = []
        if old_group.name:
            text_parts.append(old_group.name)
        if old_group.description:
            text_parts.append(old_group.description)
        combined_text = '\n'.join(text_parts) if text_parts else None
        
        message = Message(
            id=old_group.id,
            text=combined_text,
            actor_id=old_group.actor_id,
            created_at=old_group.created_at,
            updated_at=old_group.updated_at
        )
        new_db.add(message)
        new_db.flush()
        message_count += 1
        
        media_in_group = old_db.query(OldMedia).filter(OldMedia.group_id == old_group.id).all()
        for idx, old_media in enumerate(media_in_group):
            message_media = NewMessageMedia(
                message_id=message.id,
                media_id=old_media.id,
                position=idx,
                created_at=old_media.created_at
            )
            new_db.add(message_media)
            relation_count += 1
    
    new_db.commit()
    print(f"Migrated {message_count} messages (from groups)")
    print(f"Migrated {relation_count} message-media relations")

def run_migration():
    print("Starting database migration...")
    print("=" * 50)
    
    old_db = SessionLocal()
    new_db = NewSessionLocal()
    
    try:
        print("Clearing existing data in new database...")
        new_db.query(NewMessageMedia).delete()
        new_db.query(Message).delete()
        new_db.query(NewMedia).delete()
        new_db.query(NewActor).delete()
        new_db.commit()
        print("Cleared existing data")
        
        migrate_actors(old_db, new_db)
        migrate_media(old_db, new_db)
        migrate_messages_and_relations(old_db, new_db)
        
        print("=" * 50)
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        new_db.rollback()
        raise
    finally:
        old_db.close()
        new_db.close()

if __name__ == "__main__":
    run_migration()
