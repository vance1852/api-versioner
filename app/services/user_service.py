from sqlalchemy.orm import Session
from app.models import User
from typing import List, Optional


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


def create_user(db: Session, first_name: str, last_name: str, display_name: Optional[str], email: str) -> User:
    if display_name is None:
        display_name = f"{first_name} {last_name}"
    db_user = User(
        first_name=first_name,
        last_name=last_name,
        display_name=display_name,
        email=email,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True
