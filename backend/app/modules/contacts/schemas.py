import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ContactCreate(BaseModel):
    display_name: Annotated[str, Field(min_length=1, max_length=120)]
    phone_e164: str | None = None
    email: EmailStr | None = None
    preferred_lang: Literal["auto", "en", "si", "ta"] | None = None
    notes: Annotated[str, Field(max_length=1000)] | None = None

    @field_validator("phone_e164")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if not v:
            return None
        # Enforce international format: + followed by 1 to 15 digits
        import re

        if not re.match(r"^\+[1-9]\d{1,14}$", v):
            raise ValueError("Phone number must be in E.164 format (e.g. +94771234567).")
        return v


class ContactUpdate(BaseModel):
    display_name: Annotated[str, Field(min_length=1, max_length=120)] | None = None
    phone_e164: str | None = None
    email: EmailStr | None = None
    preferred_lang: Literal["auto", "en", "si", "ta"] | None = None
    notes: Annotated[str, Field(max_length=1000)] | None = None
    expected_version: int

    @field_validator("phone_e164")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
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
    phone_e164: str | None
    email: str | None
    preferred_lang: str | None
    notes: str | None
    status: str
    version: int
    created_at: datetime
    updated_at: datetime
