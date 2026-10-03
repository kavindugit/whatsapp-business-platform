import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TenantCreate(BaseModel):
    slug: Annotated[str, Field(pattern=r"^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])?$")]
    display_name: Annotated[str, Field(min_length=1, max_length=120)]
    legal_name: Annotated[str, Field(max_length=200)] | None = None
    industry_tag: str
    owner_email: EmailStr | None = None
    owner_display_name: str | None = None
    owner_password: str | None = None
    package_code: str = "starter"


class TenantStatusUpdate(BaseModel):
    status: Literal["active", "suspended"]
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
    legal_name: str | None
    industry_tag: str
    status: str
    version: int
    created_at: datetime


class BusinessSettingsUpdate(BaseModel):
    business_name: Annotated[str, Field(min_length=1, max_length=120)]
    public_email: EmailStr | None = None
    public_phone: str | None = None
    address_text: Annotated[str, Field(max_length=1000)] | None = None
    time_zone: str = "Asia/Colombo"
    currency: str = "LKR"
    reply_language: Literal["auto", "en", "si", "ta"] = "auto"
    opening_hours: dict[str, Any] = {}
    escalation_text: Annotated[str, Field(max_length=1000)] | None = None
    expected_version: int


class BusinessSettingsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    tenant_id: uuid.UUID
    business_name: str
    public_email: str | None
    public_phone: str | None
    address_text: str | None
    time_zone: str
    currency: str
    reply_language: str
    opening_hours: dict[str, Any]
    escalation_text: str | None
    version: int


class MemberDTO(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str
    role: str
    status: str
    created_at: datetime
