"""Transaction boundary helpers for synchronous application use cases."""
from sqlalchemy.orm import Session


def commit(db: Session) -> None:
    """Finish a use case, guaranteeing rollback when commit fails."""
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
