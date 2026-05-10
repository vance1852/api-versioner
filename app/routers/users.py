from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import get_db
from app.services import user_service
from app.version_config import (
    LATEST_VERSION,
    transform_response,
    transform_create_input,
    transform_update_input,
)

router = APIRouter()


def _user_to_dict(user) -> Dict[str, Any]:
    return {
        "id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "display_name": user.display_name,
        "email": user.email,
    }


def _get_version(request: Request) -> int:
    return getattr(request.state, "api_version", LATEST_VERSION)


@router.get("/users", response_model=List[Dict[str, Any]])
def list_users(request: Request, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    version = _get_version(request)
    users = user_service.get_users(db, skip=skip, limit=limit)
    return [transform_response(_user_to_dict(u), version) for u in users]


@router.get("/users/{user_id}", response_model=Dict[str, Any])
def get_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    version = _get_version(request)
    user = user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return transform_response(_user_to_dict(user), version)


@router.post("/users", response_model=Dict[str, Any], status_code=201)
def create_user(request: Request, body: Dict[str, Any], db: Session = Depends(get_db)):
    version = _get_version(request)
    internal_data = transform_create_input(body, version)
    user = user_service.create_user(
        db=db,
        first_name=internal_data.get("first_name", ""),
        last_name=internal_data.get("last_name", ""),
        display_name=internal_data.get("display_name"),
        email=internal_data.get("email", ""),
    )
    return transform_response(_user_to_dict(user), version)


@router.put("/users/{user_id}", response_model=Dict[str, Any])
def update_user(request: Request, user_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    version = _get_version(request)
    internal_data = transform_update_input(body, version)
    user = user_service.update_user(db, user_id, **internal_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return transform_response(_user_to_dict(user), version)


@router.delete("/users/{user_id}")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"detail": "User deleted"}
