from typing import List, Optional, Dict, Any, Type
from sqlalchemy.orm import Session
from app.models import Base


class BaseService:
    @staticmethod
    def get_all(db: Session, model: Type[Base]) -> List[Base]:
        return db.query(model).all()

    @staticmethod
    def get_by_id(db: Session, model: Type[Base], id: int) -> Optional[Base]:
        return db.query(model).filter(model.id == id).first()

    @staticmethod
    def create(db: Session, model: Type[Base], create_data: Dict[str, Any]) -> Base:
        db_item = model(**create_data)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def update(db: Session, model: Type[Base], id: int, update_data: Dict[str, Any]) -> Optional[Base]:
        db_item = db.query(model).filter(model.id == id).first()
        if not db_item:
            return None

        for key, value in update_data.items():
            setattr(db_item, key, value)

        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, model: Type[Base], id: int) -> bool:
        db_item = db.query(model).filter(model.id == id).first()
        if not db_item:
            return False

        db.delete(db_item)
        db.commit()
        return True
