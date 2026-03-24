import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.new_models import NewSessionLocal, Message

def verify_migration():
    print("Verifying migration...")
    db = NewSessionLocal()
    
    try:
        # Get a sample of messages to verify
        messages = db.query(Message).limit(5).all()
        print(f"Sample of {len(messages)} messages:")
        print("=" * 60)
        
        for msg in messages:
            print(f"Message ID: {msg.id}")
            print(f"Text: {repr(msg.text)}")
            print(f"Actor ID: {msg.actor_id}")
            print(f"Created at: {msg.created_at}")
            print("-" * 60)
        
        # Count total messages
        total_messages = db.query(Message).count()
        print(f"Total messages: {total_messages}")
        
    finally:
        db.close()

if __name__ == "__main__":
    verify_migration()
