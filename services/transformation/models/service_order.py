from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class ServiceType(str, Enum):
    MAIN = "MAIN"
    TRUCKING = "TRUCKING"
    ADDITIONAL = "ADDITIONAL"


class TransportType(str, Enum):
    KV = "KV"
    STANDARD = "Standard"


class LoadingStatus(str, Enum):
    BELADEN = "beladen"
    LEER = "leer"


class TypeOfTrip(str, Enum):
    ZUSTELLUNG = "Zustellung"
    ABHOLUNG = "Abholung"
    LEERCONTAINER = "Leercontainer"


class ServiceOrderOutput(BaseModel):
    """Transformed service order output"""
    service_type: ServiceType
    order_reference: str
    customer_code: str
    freightpayer_code: str

    # Container information
    container_type_iso_code: str
    gross_weight: int = Field(..., description="Calculated from tare + payload")
    length: str = Field(..., description="Derived from container type")
    loading_status: LoadingStatus
    transport_type: TransportType

    # Route information
    departure_station: str
    destination_station: str
    departure_date: datetime

    # Geography & Route Details (from Order JSON - no hardcoded values)
    departure_country: str = Field(..., description="From Container.TakeOver.DepartureCountryIsoCode")
    destination_country: str = Field(..., description="From Container.HandOver.DestinationCountryIsoCode")
    transport_direction: str = Field(..., description="From Container.TransportDirection (Export/Import/Domestic)")
    tariff_point_dep: Optional[str] = Field(None, description="From TruckingServices.Waypoints.TariffPoint (departure)")
    tariff_point_dest: Optional[str] = Field(None, description="From TruckingServices.Waypoints.TariffPoint (destination)")
    customer_group: Optional[str] = Field(None, description="From database lookup or empty for generic XLSX match")

    # Service-specific fields
    type_of_trip: Optional[TypeOfTrip] = None
    trucking_code: Optional[str] = None
    additional_service_code: Optional[str] = None
    quantity: int = Field(default=1)

    # Flags
    dangerous_goods_flag: bool

    # Source data for traceability
    original_order_reference: str
    transformation_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class TransformationResult(BaseModel):
    """Complete transformation result containing all service orders"""
    operational_order_id: str
    main_service: ServiceOrderOutput
    trucking_services: List[ServiceOrderOutput]
    additional_services: List[ServiceOrderOutput]
    transformation_summary: dict[str, Any]
    processing_time_ms: float