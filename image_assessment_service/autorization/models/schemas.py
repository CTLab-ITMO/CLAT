from typing import Optional, List
from pydantic import BaseModel, EmailStr


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner_id: int

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

UserAuth = UserCreate

class UserOut(UserBase):
    id: int
    nickname: str
    is_active: bool

    class Config:
        from_attributes = True

ResetRequest = UserBase

class ResetConfirm(BaseModel):
    token: str
    new_password: str

class LightUser(UserBase):
    id: int

class User(UserBase):
    id: int
    is_active: bool
    items: List[Item] = []

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenUuid(BaseModel):
    access_token: str
    session_id: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

class Inited(BaseModel):
    inited: bool
