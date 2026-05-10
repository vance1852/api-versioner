from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, EmailStr


class UserCreateV1(BaseModel):
    full_name: str
    email: EmailStr


class UserCreateV2(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr


class UserCreateV3(BaseModel):
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    email: EmailStr


class UserUpdateV1(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserUpdateV2(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserUpdateV3(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
