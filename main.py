from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from version_config import version_manager
from version_middleware import VersionMiddleware
from database import get_db, UserRepository

app = FastAPI(title="API Version Compatibility Layer", version="1.0.0")

app.add_middleware(VersionMiddleware)


class VersionedResponse(JSONResponse):
    def __init__(self, content: Any, request: Request, status_code: int = 200, **kwargs):
        from_version = version_manager.latest_version
        to_version = request.state.api_version

        if isinstance(content, list):
            downgraded = [
                version_manager.downgrade_data(item, from_version, to_version)
                for item in content
            ]
        else:
            downgraded = version_manager.downgrade_data(content, from_version, to_version)

        super().__init__(content=downgraded, status_code=status_code, **kwargs)


def get_upgraded_data(request: Request) -> Dict[str, Any]:
    async def _get_data():
        return await request.json()

    import asyncio
    try:
        data = asyncio.run(_get_data())
    except:
        data = {}

    from_version = request.state.api_version
    to_version = version_manager.latest_version

    return version_manager.upgrade_data(data, from_version, to_version)


@app.get("/api/versions")
async def list_versions():
    return {"versions": version_manager.get_all_versions()}


@app.get("/api/versions/{version}/changelog")
async def get_version_changelog(version: int):
    changelog = version_manager.get_changelog(version)
    if changelog is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"version": version, "changelog": changelog}


@app.get("/users")
async def list_users(request: Request, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    users = repo.list_all()
    return VersionedResponse(users, request)


@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return VersionedResponse(user, request)


@app.post("/users", status_code=201)
async def create_user(request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    from_version = request.state.api_version
    to_version = version_manager.latest_version
    upgraded_data = version_manager.upgrade_data(body, from_version, to_version)

    if "display_name" not in upgraded_data or not upgraded_data["display_name"]:
        upgraded_data["display_name"] = f"{upgraded_data.get('first_name', '')} {upgraded_data.get('last_name', '')}".strip()

    repo = UserRepository(db)
    user = repo.create(upgraded_data)
    return VersionedResponse(user, request, status_code=201)


@app.put("/users/{user_id}")
async def update_user(user_id: int, request: Request, db: Session = Depends(get_db)):
    body = await request.json()
    from_version = request.state.api_version
    to_version = version_manager.latest_version
    upgraded_data = version_manager.upgrade_data(body, from_version, to_version)

    repo = UserRepository(db)
    user = repo.update(user_id, upgraded_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return VersionedResponse(user, request)


@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    repo = UserRepository(db)
    success = repo.delete(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None


@app.get("/")
async def root():
    return {
        "message": "API Version Compatibility Layer",
        "latest_version": version_manager.latest_version,
        "docs": "/docs",
    }
