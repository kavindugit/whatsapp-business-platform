from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import Dict, Any, List

class PackageVersionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    version: int
    currency: str
    monthly_price: int
    setup_price: int
    staff_limit: int
    number_limit: int
    feature_permissions: Dict[str, Any]
    metric_limits: Dict[str, Any]

class PackageDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    code: str
    name: str
    release_status: str
    description: str
    versions: List[PackageVersionDTO] = []

class SubscriptionDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    tenant_id: uuid.UUID
    package_version_id: uuid.UUID
    status: str
    period_start: datetime
    period_end: datetime
    anchor_day: int
    created_at: datetime
    
    # We will extend this manually in the router response to include "usage": "N/A"
    
class SubscriptionDetailDTO(BaseModel):
    subscription: SubscriptionDTO
    package: PackageDTO
    version: int
    monthly_price: int
    setup_price: int
    staff_limit: int
    number_limit: int
    feature_permissions: Dict[str, Any]
    metric_limits: Dict[str, Any]
    usage: str = "N/A"
