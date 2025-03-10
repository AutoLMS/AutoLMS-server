from typing import Optional
from pydantic import BaseModel, EmailStr

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserBase(BaseModel):
    email: Optional[EmailStr] = None

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserLogin(UserBase):
    email: EmailStr
    password: str

class UserOut(UserBase):
    id: str
    email: EmailStr
