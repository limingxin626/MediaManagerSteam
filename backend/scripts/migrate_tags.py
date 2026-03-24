import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, Column, Integer, String, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import ForeignKey

OLD_DB_URL = "sqlite:///./db.sqlite3"
NEW_DB_URL = "sqlite:///./db_new.sqlite3"

old_engine = create_engine(OLD_DB_URL, connect_args={"check_same_thread": False})
new_engine = create_engine(NEW_DB_URL, connect_args={"check_same_thread": False})

OldSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=old_engine)
NewSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=new_engine)

OldBase = declarative_base()
NewBase = declarative_base()

class OldTagging(OldBase):
    __tablename__ = "tagging"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    category = Column(String(64), default='body', nullable=True)

class OldMediaTags(OldBase):
    __tablename__ = "media_tags"
    media_id = Column(Integer, ForeignKey("media.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tagging.id"), primary_key=True)

class OldMedia(OldBase):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("group.id"), nullable=True)

class OldGroup(OldBase):
    __tablename__ = "group"
    
    id = Column(Integer, primary_key=True, index=True)

message_tag = Table(
    'message_tag',
    NewBase.metadata,
    Column('message_id', Integer, ForeignKey('message.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)

class NewTag(NewBase):
    __tablename__ = "tag"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    category = Column(String(128), nullable=True, index=True)

class NewMessage(NewBase):
    __tablename__ = "message"
    
    id = Column(Integer, primary_key=True, index=True)

class NewMessageMedia(NewBase):
    __tablename__ = "message_media"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("message.id"), nullable=False, index=True)
    media_id = Column(Integer, ForeignKey("media.id"), nullable=False, index=True)

class NewMedia(NewBase):
    __tablename__ = "media"
    
    id = Column(Integer, primary_key=True, index=True)

def migrate_tags(old_db, new_db):
    print("Migrating tags...")
    old_tags = old_db.query(OldTagging).all()
    
    for old_tag in old_tags:
        new_tag = NewTag(
            id=old_tag.id,
            name=old_tag.name,
            category=old_tag.category
        )
        new_db.merge(new_tag)
    
    new_db.commit()
    print(f"Migrated {len(old_tags)} tags")

def migrate_message_tag_relations(old_db, new_db):
    print("Migrating message-tag relations...")
    
    old_media_tags = old_db.query(OldMediaTags).all()
    media_to_tags = {}
    for mt in old_media_tags:
        if mt.media_id not in media_to_tags:
            media_to_tags[mt.media_id] = set()
        media_to_tags[mt.media_id].add(mt.tag_id)
    
    message_media_relations = new_db.query(NewMessageMedia).all()
    
    message_tag_relations = set()
    
    for mm in message_media_relations:
        media_id = mm.media_id
        message_id = mm.message_id
        
        if media_id in media_to_tags:
            for tag_id in media_to_tags[media_id]:
                message_tag_relations.add((message_id, tag_id))
    
    for message_id, tag_id in message_tag_relations:
        new_db.execute(
            message_tag.insert().values(message_id=message_id, tag_id=tag_id)
        )
    
    new_db.commit()
    print(f"Migrated {len(message_tag_relations)} message-tag relations")
    print(f"(From {len(message_media_relations)} message-media relations)")

def run_migration():
    print("Starting tag migration...")
    print("=" * 50)
    
    print("Creating tables in new database...")
    NewBase.metadata.create_all(bind=new_engine)
    print("Tables created")
    
    old_db = OldSessionLocal()
    new_db = NewSessionLocal()
    
    try:
        migrate_tags(old_db, new_db)
        migrate_message_tag_relations(old_db, new_db)
        
        print("=" * 50)
        print("Tag migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        new_db.rollback()
        raise
    finally:
        old_db.close()
        new_db.close()

if __name__ == "__main__":
    run_migration()
