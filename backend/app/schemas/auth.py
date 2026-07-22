from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TenantCreate(BaseModel):
    name: str

class TenantResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    company_name: str
    email: EmailStr
    password: str
    full_name: str
    role: Optional[str] = "CEO"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    role: str
    created_at: datetime
    tenant: TenantResponse

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
