from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from sqlalchemy.orm import Session

from .database import User, create_tables, get_db, user_to_dict
from .middleware import VersionMiddleware, version_dependency
from .schemas import (
    UserCreateV1,
    UserCreateV2,
    UserCreateV3,
    UserUpdateV1,
    UserUpdateV2,
    UserUpdateV3,
)
from .transformer import parse_body_for_version, transform_list_to_version, transform_to_version
from .versions import get_all_versions, get_version_config

app = FastAPI(title="API Versioning Demo")

app.add_middleware(VersionMiddleware)


@app.on_event("startup")
def on_startup():
    create_tables()


def _get_create_schema(version: str):
    if version == "1":
        return UserCreateV1
    elif version == "2":
        return UserCreateV2
    return UserCreateV3


def _get_update_schema(version: str):
    if version == "1":
        return UserUpdateV1
    elif version == "2":
        return UserUpdateV2
    return UserUpdateV3


@app.get("/api/versions")
def list_versions():
    return {"versions": get_all_versions()}


@app.get("/api/versions/{version}/changelog")
def get_changelog(version: str):
    cfg = get_version_config(version)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")
    return {
        "version": cfg.version,
        "status": cfg.status,
        "sunset_date": cfg.sunset_date,
        "changelog": cfg.changelog,
    }


@app.post("/users")
async def create_user(
    request: Request,
    db: Session = Depends(get_db),
    version: str = Depends(version_dependency),
):
    raw_body = await request.json()
    parsed = parse_body_for_version(raw_body, version)

    existing = db.query(User).filter(User.email == parsed.get("email")).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        first_name=parsed.get("first_name", ""),
        last_name=parsed.get("last_name", ""),
        display_name=parsed.get("display_name", ""),
        email=parsed.get("email", ""),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return transform_to_version(user_to_dict(user), version)


@app.get("/users")
def list_users(
    db: Session = Depends(get_db),
    version: str = Depends(version_dependency),
):
    users = db.query(User).all()
    return transform_list_to_version([user_to_dict(u) for u in users], version)


@app.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    version: str = Depends(version_dependency),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return transform_to_version(user_to_dict(user), version)


@app.put("/users/{user_id}")
async def update_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    version: str = Depends(version_dependency),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    raw_body = await request.json()
    parsed = parse_body_for_version(raw_body, version)

    if "first_name" in parsed:
        user.first_name = parsed["first_name"]
    if "last_name" in parsed:
        user.last_name = parsed["last_name"]
    if "display_name" in parsed:
        user.display_name = parsed["display_name"]
    if "email" in parsed:
        user.email = parsed["email"]

    db.commit()
    db.refresh(user)

    return transform_to_version(user_to_dict(user), version)


@app.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    version: str = Depends(version_dependency),
):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}
