from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class Customer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., alias="Code", description="Customer code")
    name: Optional[str] = Field(None, alias="Name", description="Customer name")


class Freightpayer(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., alias="Code", description="Freightpayer code")
    name: Optional[str] = Field(None, alias="Name", description="Freightpayer name")


class Consignee(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., alias="Code", description="Consignee code")
    name: Optional[str] = Field(None, alias="Name", description="Consignee name")


class Terminal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    railway_station_number: str = Field(..., alias="RailwayStationNumber")


class RailService(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    departure_date: datetime = Field(..., alias="DepartureDate")
    departure_terminal: Terminal = Field(..., alias="DepartureTerminal")
    destination_terminal: Terminal = Field(..., alias="DestinationTerminal")


class Waypoint(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sequence_number: str = Field(..., alias="SequenceNumber")
    is_main_address: str = Field(..., alias="IsMainAdress")
    waypoint_type: str = Field(..., alias="WayPointType")
    tariff_point: str = Field(..., alias="TariffPoint")
    address_code: str = Field(..., alias="AdressCode")
    delivery_date: Optional[datetime] = Field(None, alias="DeliveryDate")


class TruckingService(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    sequence_number: str = Field(..., alias="SequenceNumber")
    type: str = Field(..., alias="Type")
    trucking_code: str = Field(..., alias="TruckingCode")
    waypoints: List[Waypoint] = Field(..., alias="Waypoints")


class AdditionalService(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = Field(..., alias="Code", description="Additional service code")
    amount: Optional[str] = Field(None, alias="Amount", description="Amount/quantity (brutto)")
    unit: Optional[str] = Field(None, alias="Unit", description="Unit of measurement")


class TakeOver(BaseModel):
    """Container take-over location (departure)"""
    model_config = ConfigDict(populate_by_name=True)

    departure_country_iso_code: str = Field(..., alias="DepartureCountryIsoCode", description="Departure country ISO code")


class HandOver(BaseModel):
    """Container hand-over location (destination)"""
    model_config = ConfigDict(populate_by_name=True)

    destination_country_iso_code: str = Field(..., alias="DestinationCountryIsoCode", description="Destination country ISO code")


class Container(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    position: str = Field(..., alias="Position")
    transport_direction: str = Field(..., alias="TransportDirection")
    container_type_iso_code: str = Field(..., alias="ContainerTypeIsoCode")
    tare_weight: str = Field(..., alias="TareWeight")
    payload: str = Field(..., alias="Payload")
    take_over: Optional[TakeOver] = Field(None, alias="TakeOver", description="Container take-over location with country")
    hand_over: Optional[HandOver] = Field(None, alias="HandOver", description="Container hand-over location with country")
    rail_service: RailService = Field(..., alias="RailService")
    trucking_services: List[TruckingService] = Field(..., alias="TruckingServices")
    additional_services: List[AdditionalService] = Field(..., alias="AdditionalServices")
    dangerous_good_flag: str = Field(..., alias="DangerousGoodFlag")


class Order(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order_reference: str = Field(..., alias="OrderReference")
    customer: Customer = Field(..., alias="Customer")
    freightpayer: Freightpayer = Field(..., alias="Freightpayer")
    consignee: Consignee = Field(..., alias="Consignee")
    container: Container = Field(..., alias="Container")


class OperationalOrderInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    order: Order = Field(..., alias="Order")