import re
from fastapi import FastAPI, Request
from app.database import engine, Base
from app.models import User
from app.version_middleware import VersionMiddleware
from app.routers import users, versions
from app.version_config import LATEST_VERSION


Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Versioner", version="1.0.0")

app.add_middleware(VersionMiddleware)

app.include_router(users.router)
app.include_router(versions.router)


@app.get("/")
def root():
    return {
        "service": "API Versioner",
        "latest_version": LATEST_VERSION,
        "docs": "/docs",
    }
