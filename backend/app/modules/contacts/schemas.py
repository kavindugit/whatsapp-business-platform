import uuid
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, constr, field_validator

class ContactCreate(BaseModel):
    display_name: constr(min_length=1, max_length=120)
    phone_e164: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_lang: Optional[Literal['auto', 'en', 'si', 'ta']] = None
    notes: Optional[constr(max_length=1000)] = None
    
    @field_validator("phone_e164")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        # Enforce international format: + followed by 1 to 15 digits
        import re
        if not re.match(r"^\+[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in E.164 format (e.g. +94771234567).")
        return v

class ContactUpdate(BaseModel):
    display_name: Optional[constr(min_length=1, max_length=120)] = None
    phone_e164: Optional[str] = None
    email: Optional[EmailStr] = None
    preferred_lang: Optional[Literal['auto', 'en', 'si', 'ta']] = None
    notes: Optional[constr(max_length=1000)] = None
    expected_version: int

    @field_validator("phone_e164")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        import re
        if not re.match(r"^\+[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in E.164 format (e.g. +94771234567).")
        return v

class ContactAction(BaseModel):
    expected_version: int

class ContactDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tenant_id: uuid.UUID
    display_name: str
    phone_e164: Optional[str]
    email: Optional[str]
    preferred_lang: Optional[str]
    notes: Optional[str]
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
