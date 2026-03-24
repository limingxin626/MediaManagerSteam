import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import SessionLocal, Message, Actor, Media, MessageMedia
from datetime import datetime, timedelta
import shutil
from sqlalchemy import func

def backup_database():
    backup_path = 'db_new.sqlite3.backup'
    if os.path.exists(backup_path):
        os.remove(backup_path)
    shutil.copy('db_new.sqlite3', backup_path)
    print(f"Database backed up to {backup_path}")

def update_media_times(db):
    print("Updating Media created_at times...")
    
    # Get max media ID
    max_media_id = db.query(func.max(Media.id)).scalar()
    print(f"Max media ID: {max_media_id}")
    
    # Get total media count
    media_count = db.query(Media).count()
    print(f"Total media count: {media_count}")
    
    # Calculate time interval: 24 hours / 100 = 14.4 minutes per media
    interval = timedelta(minutes=14.4)
    
    # Start from current time
    current_time = datetime.utcnow()
    print(f"Starting time: {current_time}")
    
    # Update media times in reverse ID order
    media_list = db.query(Media).order_by(Media.id.desc()).all()
    
    for i, media in enumerate(media_list):
        # Calculate time for this media
        media_time = current_time - (i * interval)
        media.created_at = media_time
        media.updated_at = media_time
        
        if (i + 1) % 1000 == 0:
            print(f"Updated {i + 1}/{media_count} media records")
    
    db.commit()
    print(f"Updated {media_count} media records")
    
    # Show time range
    min_time = db.query(func.min(Media.created_at)).scalar()
    max_time = db.query(func.max(Media.created_at)).scalar()
    print(f"Media time range: {min_time} to {max_time}")
    print(f"Time span: {(max_time - min_time).days} days")

def update_message_times(db):
    print("\nUpdating Message created_at times...")
    
    # Get all messages
    messages = db.query(Message).all()
    message_count = len(messages)
    print(f"Total message count: {message_count}")
    
    updated_count = 0
    no_media_count = 0
    
    for message in messages:
        # Get all media associated with this message
        media_list = db.query(Media).join(MessageMedia).filter(
            MessageMedia.message_id == message.id
        ).all()
        
        if media_list:
            # Use the earliest media time as message time
            min_media_time = min(m.created_at for m in media_list)
            message.created_at = min_media_time
            message.updated_at = min_media_time
            updated_count += 1
        else:
            # For messages without media, use current time
            message.created_at = datetime.utcnow()
            message.updated_at = datetime.utcnow()
            no_media_count += 1
        
        if (updated_count + no_media_count) % 100 == 0:
            print(f"Processed {updated_count + no_media_count}/{message_count} messages")
    
    db.commit()
    print(f"Updated {updated_count} messages with media")
    print(f"Set default time for {no_media_count} messages without media")
    
    # Show time range
    min_time = db.query(func.min(Message.created_at)).scalar()
    max_time = db.query(func.max(Message.created_at)).scalar()
    print(f"Message time range: {min_time} to {max_time}")

def update_actor_times(db):
    print("\nUpdating Actor created_at times...")
    
    # Get all actors
    actors = db.query(Actor).all()
    actor_count = len(actors)
    print(f"Total actor count: {actor_count}")
    
    updated_count = 0
    no_message_count = 0
    
    for actor in actors:
        # Get all messages associated with this actor
        messages = db.query(Message).filter(Message.actor_id == actor.id).all()
        
        if messages:
            # Use the earliest message time as actor time
            min_message_time = min(m.created_at for m in messages)
            actor.created_at = min_message_time
            actor.updated_at = min_message_time
            updated_count += 1
        else:
            # For actors without messages, use current time
            actor.created_at = datetime.utcnow()
            actor.updated_at = datetime.utcnow()
            no_message_count += 1
        
        if (updated_count + no_message_count) % 50 == 0:
            print(f"Processed {updated_count + no_message_count}/{actor_count} actors")
    
    db.commit()
    print(f"Updated {updated_count} actors with messages")
    print(f"Set default time for {no_message_count} actors without messages")
    
    # Show time range
    min_time = db.query(func.min(Actor.created_at)).scalar()
    max_time = db.query(func.max(Actor.created_at)).scalar()
    print(f"Actor time range: {min_time} to {max_time}")

def update_message_media_times(db):
    print("\nUpdating MessageMedia created_at times...")
    
    # Get all message_media records
    message_media_list = db.query(MessageMedia).all()
    count = len(message_media_list)
    print(f"Total message_media count: {count}")
    
    for i, mm in enumerate(message_media_list):
        # Get the associated message
        message = db.query(Message).filter(Message.id == mm.message_id).first()
        if message:
            mm.created_at = message.created_at
        
        if (i + 1) % 1000 == 0:
            print(f"Updated {i + 1}/{count} message_media records")
    
    db.commit()
    print(f"Updated {count} message_media records")

def verify_changes(db):
    print("\n" + "="*60)
    print("Verification Results:")
    print("="*60)
    
    # Check media times
    media_count = db.query(Media).count()
    distinct_media_times = db.query(func.count(func.distinct(Media.created_at))).scalar()
    min_media_time = db.query(func.min(Media.created_at)).scalar()
    max_media_time = db.query(func.max(Media.created_at)).scalar()
    print(f"\nMedia:")
    print(f"  Total: {media_count}")
    print(f"  Distinct times: {distinct_media_times}")
    print(f"  Time range: {min_media_time} to {max_media_time}")
    
    # Check message times
    message_count = db.query(Message).count()
    distinct_message_times = db.query(func.count(func.distinct(Message.created_at))).scalar()
    min_message_time = db.query(func.min(Message.created_at)).scalar()
    max_message_time = db.query(func.max(Message.created_at)).scalar()
    print(f"\nMessage:")
    print(f"  Total: {message_count}")
    print(f"  Distinct times: {distinct_message_times}")
    print(f"  Time range: {min_message_time} to {max_message_time}")
    
    # Check actor times
    actor_count = db.query(Actor).count()
    distinct_actor_times = db.query(func.count(func.distinct(Actor.created_at))).scalar()
    min_actor_time = db.query(func.min(Actor.created_at)).scalar()
    max_actor_time = db.query(func.max(Actor.created_at)).scalar()
    print(f"\nActor:")
    print(f"  Total: {actor_count}")
    print(f"  Distinct times: {distinct_actor_times}")
    print(f"  Time range: {min_actor_time} to {max_actor_time}")
    
    # Check message_media times
    message_media_count = db.query(MessageMedia).count()
    distinct_mm_times = db.query(func.count(func.distinct(MessageMedia.created_at))).scalar()
    print(f"\nMessageMedia:")
    print(f"  Total: {message_media_count}")
    print(f"  Distinct times: {distinct_mm_times}")

def main():
    print("="*60)
    print("Database Time Adjustment Script")
    print("="*60)
    
    # Backup database
    backup_database()
    
    db = SessionLocal()
    
    try:
        # Step 1: Update media times
        update_media_times(db)
        
        # Step 2: Update message times based on media
        update_message_times(db)
        
        # Step 3: Update actor times based on messages
        update_actor_times(db)
        
        # Step 4: Update message_media times
        update_message_media_times(db)
        
        # Verify changes
        verify_changes(db)
        
        print("\n" + "="*60)
        print("Time adjustment completed successfully!")
        print("="*60)
        
    except Exception as e:
        print(f"\nError: {e}")
        db.rollback()
        print("Changes rolled back. Database restored.")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
