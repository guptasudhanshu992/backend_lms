from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    consent: bool = False

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    role: str
    consent: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login: Optional[datetime]
    oauth_provider: Optional[str]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[str] = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class RoleOut(RoleBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []


class GroupOut(GroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class SessionOut(BaseModel):
    id: int
    user_id: int
    user_agent: Optional[str]
    ip: Optional[str]
    device_info: Optional[str]
    created_at: datetime
    last_active_at: datetime
    revoked: bool

    class Config:
        from_attributes = True


class AuditLogOut(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    resource: Optional[str]
    ip: Optional[str]
    status: str
    meta: str
    created_at: datetime

    class Config:
        from_attributes = True


class GDPRDataExport(BaseModel):
    user: UserOut
    sessions: List[SessionOut]
    audit_logs: List[AuditLogOut]
