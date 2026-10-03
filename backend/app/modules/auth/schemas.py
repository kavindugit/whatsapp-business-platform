import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserSummary(BaseModel):
    id: str
    email: str
    display_name: str
    system_role: str | None


class MembershipSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tenant_id: uuid.UUID
    display_name: str
    role: str
    status: str
    created_at: datetime


class AuthResponse(BaseModel):
    user: UserSummary
    csrf_token: str
    memberships: list[MembershipSummary] = []


class MeResponse(BaseModel):
    user: UserSummary
    csrf_token: str
    memberships: list[MembershipSummary] = []
