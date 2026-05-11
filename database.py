from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import List, Optional, Dict, Any

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    display_name = Column(String, index=True)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserRepository:
    def __init__(self, db):
        self.db = db

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        db_user = User(
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            display_name=data.get("display_name", ""),
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return self._to_dict(db_user)

    def get_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            return self._to_dict(user)
        return None

    def list_all(self) -> List[Dict[str, Any]]:
        users = self.db.query(User).all()
        return [self._to_dict(u) for u in users]

    def update(self, user_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return self._to_dict(user)

    def delete(self, user_id: int) -> bool:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def _to_dict(self, user: User) -> Dict[str, Any]:
        return {
            "id": user.id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
        }
