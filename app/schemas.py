from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreateV3(BaseModel):
    first_name: str
    last_name: str
    display_name: Optional[str] = None
    email: str


class UserCreateV2(BaseModel):
    first_name: str
    last_name: str
    email: str


class UserCreateV1(BaseModel):
    full_name: str
    email: str


class UserUpdateV3(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    email: Optional[str] = None


class UserUpdateV2(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None


class UserUpdateV1(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None


class UserResponseV3(BaseModel):
    id: int
    first_name: str
    last_name: str
    display_name: Optional[str]
    email: str


class UserResponseV2(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str


class UserResponseV1(BaseModel):
    id: int
    full_name: str
    email: str
