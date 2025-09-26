from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class Customer(BaseModel):
    code: str = Field(..., description="Customer code")
    name: Optional[str] = Field(None, description="Customer name")


class Freightpayer(BaseModel):
    code: str = Field(..., description="Freightpayer code")
    name: Optional[str] = Field(None, description="Freightpayer name")


class Consignee(BaseModel):
    code: str = Field(..., description="Consignee code")
    name: Optional[str] = Field(None, description="Consignee name")


class Terminal(BaseModel):
    railway_station_number: str = Field(..., alias="RailwayStationNumber")


class RailService(BaseModel):
    departure_date: datetime = Field(..., alias="DepartureDate")
    departure_terminal: Terminal = Field(..., alias="DepartureTerminal")
    destination_terminal: Terminal = Field(..., alias="DestinationTerminal")


class Waypoint(BaseModel):
    sequence_number: str = Field(..., alias="SequenceNumber")
    is_main_address: str = Field(..., alias="IsMainAdress")
    waypoint_type: str = Field(..., alias="WayPointType")
    tariff_point: str = Field(..., alias="TariffPoint")
    address_code: str = Field(..., alias="AdressCode")
    delivery_date: Optional[datetime] = Field(None, alias="DeliveryDate")


class TruckingService(BaseModel):
    sequence_number: str = Field(..., alias="SequenceNumber")
    type: str = Field(..., alias="Type")
    trucking_code: str = Field(..., alias="TruckingCode")
    waypoints: List[Waypoint] = Field(..., alias="Waypoints")


class AdditionalService(BaseModel):
    code: str = Field(..., description="Additional service code")


class Container(BaseModel):
    position: str = Field(..., alias="Position")
    transport_direction: str = Field(..., alias="TransportDirection")
    container_type_iso_code: str = Field(..., alias="ContainerTypeIsoCode")
    tare_weight: str = Field(..., alias="TareWeight")
    payload: str = Field(..., alias="Payload")
    rail_service: RailService = Field(..., alias="RailService")
    trucking_services: List[TruckingService] = Field(..., alias="TruckingServices")
    additional_services: List[AdditionalService] = Field(..., alias="AdditionalServices")
    dangerous_good_flag: str = Field(..., alias="DangerousGoodFlag")


class Order(BaseModel):
    order_reference: str = Field(..., alias="OrderReference")
    customer: Customer = Field(..., alias="Customer")
    freightpayer: Freightpayer = Field(..., alias="Freightpayer")
    consignee: Consignee = Field(..., alias="Consignee")
    container: Container = Field(..., alias="Container")


class OperationalOrderInput(BaseModel):
    order: Order = Field(..., alias="Order")

    class Config:
        populate_by_name = True