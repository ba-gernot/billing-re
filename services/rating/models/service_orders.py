"""
Service order models for the rating service
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum


class ServiceType(str, Enum):
    MAIN = "MAIN"
    TRUCKING = "TRUCKING"
    ADDITIONAL = "ADDITIONAL"


class ServiceOrder(BaseModel):
    """
    Service order model for rating processing
    """
    service_type: ServiceType
    service_code: str
    quantity: int = 1
    unit_price: float = 0.0

    # Main service specific fields
    gross_weight: Optional[int] = None
    weight_class: Optional[str] = None
    transport_direction: Optional[str] = None
    loading_status: Optional[str] = None
    dangerous_goods: Optional[bool] = None
    route_data: Optional[Dict[str, Any]] = None

    # Trucking service specific fields
    trucking_code: Optional[str] = None
    station: Optional[str] = None

    # Additional service specific fields
    additional_service_code: Optional[str] = None

    # Metadata
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        use_enum_values = True