from pydantic import BaseModel, ConfigDict, Field, EmailStr, constr
from typing import Optional, Literal, Any
import uuid
from datetime import datetime

class TenantCreate(BaseModel):
    slug: constr(pattern=r'^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$')
    display_name: constr(min_length=1, max_length=120)
    legal_name: Optional[constr(max_length=200)] = None
    industry_tag: str
    owner_email: Optional[EmailStr] = None
    owner_display_name: Optional[str] = None
    owner_password: Optional[str] = None
    package_code: str = "starter"


class TenantStatusUpdate(BaseModel):
    status: Literal['active', 'suspended']
    reason: str = ""
    version: int = 0  # frontend sends version
    expected_version: int = 0  # backend uses expected_version

    def model_post_init(self, __context: Any) -> None:
        # Allow frontend to send either 'version' or 'expected_version'
        if self.version and not self.expected_version:
            self.expected_version = self.version


class TenantDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    display_name: str
    legal_name: Optional[str]
    industry_tag: str
    status: str
    version: int
    created_at: datetime

class BusinessSettingsUpdate(BaseModel):
    business_name: constr(min_length=1, max_length=120)
    public_email: Optional[EmailStr] = None
    public_phone: Optional[str] = None
    address_text: Optional[constr(max_length=1000)] = None
    time_zone: str = "Asia/Colombo"
    currency: str = "LKR"
    reply_language: Literal['auto', 'en', 'si', 'ta'] = "auto"
    opening_hours: dict = {}
    escalation_text: Optional[constr(max_length=1000)] = None
    expected_version: int

class BusinessSettingsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tenant_id: uuid.UUID
    business_name: str
    public_email: Optional[str]
    public_phone: Optional[str]
    address_text: Optional[str]
    time_zone: str
    currency: str
    reply_language: str
    opening_hours: dict
    escalation_text: Optional[str]
    version: int

class MemberDTO(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str
    status: str
    created_at: datetime
