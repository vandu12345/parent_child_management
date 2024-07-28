from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ParentCreate(BaseModel):
    email: EmailStr
    password: str


class ParentLogin(BaseModel):
    email: EmailStr
    password: str


class ParentUpdate(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None


class Parent(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    age: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None
    profile_photo: Optional[str] = None


class ChildCreate(BaseModel):
    name: str
    date_of_birth: datetime
    parent_id: int


class ChildUpdate(BaseModel):
    id: int
    name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    parent_id: int


class Child(BaseModel):
    id: int
    parent_id: int
    name: str
    date_of_birth: datetime
    created_at: datetime
    updated_at: datetime
