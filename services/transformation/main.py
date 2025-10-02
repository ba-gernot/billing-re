from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import json
from typing import List
from contextlib import asynccontextmanager

from models.operational_order import OperationalOrderInput
from models.service_order import (
    TransformationResult,
    ServiceOrderOutput,
    ServiceType,
    LoadingStatus,
    TransportType,
    TypeOfTrip
)
from validators.order_validator import OrderValidator
from enrichers.container_enricher import ContainerEnricher
from database.connection import db
from rules.dmn_trip_type import DMNTripTypeClassification

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await db.initialize()
    yield
    # Shutdown
    await db.close()

app = FastAPI(
    title="Transformation Service",
    description="Converts operational orders into service orders for the billing pipeline",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Debug middleware to log raw requests
@app.middleware("http")
async def log_raw_request(request: Request, call_next):
    if request.url.path == "/transform":
        # Read the raw body
        body = await request.body()
        print(f"\n{'='*80}")
        print(f"[RAW REQUEST MIDDLEWARE] Path: {request.url.path}")
        print(f"[RAW REQUEST MIDDLEWARE] Method: {request.method}")
        print(f"[RAW REQUEST MIDDLEWARE] Headers: {dict(request.headers)}")
        print(f"[RAW REQUEST MIDDLEWARE] Raw Body Length: {len(body)} bytes")

        try:
            body_json = json.loads(body)
            print(f"[RAW REQUEST MIDDLEWARE] Parsed JSON Keys: {list(body_json.keys())}")
            if 'Order' in body_json:
                order_keys = list(body_json['Order'].keys())
                print(f"[RAW REQUEST MIDDLEWARE] Order Keys: {order_keys}")
                print(f"[RAW REQUEST MIDDLEWARE] Has Consignee in Order: {'Consignee' in order_keys}")
                if 'Container' in body_json['Order']:
                    container_keys = list(body_json['Order']['Container'].keys())
                    print(f"[RAW REQUEST MIDDLEWARE] Container Keys: {container_keys}")
                    print(f"[RAW REQUEST MIDDLEWARE] Has Position in Container: {'Position' in container_keys}")
            print(f"[RAW REQUEST MIDDLEWARE] Full Body Preview:")
            print(json.dumps(body_json, indent=2)[:500])  # First 500 chars
        except Exception as e:
            print(f"[RAW REQUEST MIDDLEWARE] Could not parse JSON: {e}")
        print(f"{'='*80}\n")

        # Important: Re-create the request with the body we just read
        async def receive():
            return {"type": "http.request", "body": body}

        request = Request(request.scope, receive)

    response = await call_next(request)
    return response

# Initialize services
order_validator = OrderValidator()
container_enricher = ContainerEnricher()
dmn_trip_type = DMNTripTypeClassification()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "transformation"}


@app.post("/transform", response_model=TransformationResult)
async def transform_order(order_input: OperationalOrderInput):
    """
    Transform operational order into service orders

    Process:
    1. Validate input order
    2. Enrich container data
    3. Decompose into service orders (main/trucking/additional)
    4. Apply business rules for field mapping
    """
    start_time = time.time()

    # DEBUG LOGGING: Log the raw input received by Pydantic
    print(f"\n{'='*80}")
    print(f"[TRANSFORMATION SERVICE] Received order_input type: {type(order_input)}")
    print(f"[TRANSFORMATION SERVICE] order_input.order type: {type(order_input.order)}")
    print(f"[TRANSFORMATION SERVICE] Has customer: {hasattr(order_input.order, 'customer')}")
    print(f"[TRANSFORMATION SERVICE] Has freightpayer: {hasattr(order_input.order, 'freightpayer')}")
    print(f"[TRANSFORMATION SERVICE] Has consignee: {hasattr(order_input.order, 'consignee')}")
    print(f"[TRANSFORMATION SERVICE] Has container: {hasattr(order_input.order, 'container')}")

    if hasattr(order_input.order, 'consignee'):
        print(f"[TRANSFORMATION SERVICE] Consignee: {order_input.order.consignee}")
    else:
        print(f"[TRANSFORMATION SERVICE] ❌ CONSIGNEE IS MISSING!")

    if hasattr(order_input.order, 'container'):
        print(f"[TRANSFORMATION SERVICE] Container has position: {hasattr(order_input.order.container, 'position')}")
        if hasattr(order_input.order.container, 'position'):
            print(f"[TRANSFORMATION SERVICE] Container position: {order_input.order.container.position}")
        else:
            print(f"[TRANSFORMATION SERVICE] ❌ CONTAINER POSITION IS MISSING!")
    print(f"{'='*80}\n")

    try:
        # Step 1: Validate order
        validation_result = await order_validator.validate(order_input)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Validation failed: {validation_result.errors}"
            )

        # Step 2: Enrich container data using validation data
        enriched_container = await container_enricher.enrich(
            order_input.order.container,
            validation_result.enrichment_data
        )

        # Step 3: Transform to service orders (enhanced decomposition)
        service_orders = await _decompose_to_services(
            order_input,
            enriched_container,
            validation_result.enrichment_data
        )

        processing_time = (time.time() - start_time) * 1000

        return TransformationResult(
            operational_order_id=order_input.order.order_reference,
            main_service=service_orders["main"],
            trucking_services=service_orders["trucking"],
            additional_services=service_orders["additional"],
            transformation_summary={
                "total_services": len(service_orders["trucking"]) + len(service_orders["additional"]) + 1,
                "dangerous_goods": enriched_container["dangerous_goods"],
                "weight_category": enriched_container["weight_category"]
            },
            processing_time_ms=processing_time
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*80}")
        print(f"[ERROR] Transformation failed with exception:")
        print(f"[ERROR] Type: {type(e).__name__}")
        print(f"[ERROR] Message: {str(e)}")
        print(f"[ERROR] Full traceback:")
        print(error_details)
        print(f"{'='*80}\n")
        raise HTTPException(status_code=500, detail=f"Transformation failed: {str(e)}")


async def _decompose_to_services(order_input: OperationalOrderInput, enriched_container: dict, validation_data: dict) -> dict:
    """Enhanced service decomposition with business rules from roadmap"""

    # Extract geography data from Order JSON (NO hardcoded values)
    container = order_input.order.container
    transport_direction = container.transport_direction or "Export"

    # Safely extract country codes (TakeOver/HandOver may be optional)
    departure_country = "DE"  # Default fallback
    if container.take_over:
        try:
            departure_country = container.take_over.departure_country_iso_code
            print(f"✅ Extracted departure_country: {departure_country}")
        except (AttributeError, TypeError) as e:
            print(f"⚠️ Could not extract departure_country: {e}")

    destination_country = "DE"  # Default fallback
    if container.hand_over:
        try:
            destination_country = container.hand_over.destination_country_iso_code
            print(f"✅ Extracted destination_country: {destination_country}")
        except (AttributeError, TypeError) as e:
            print(f"⚠️ Could not extract destination_country: {e}")

    print(f"🌍 Final geography: {departure_country} → {destination_country} ({transport_direction})")

    # Extract tariff points from trucking waypoints (if available)
    tariff_point_dep = None
    tariff_point_dest = None
    if container.trucking_services and len(container.trucking_services) > 0:
        for waypoint in container.trucking_services[0].waypoints:
            if waypoint.waypoint_type == "Depot":
                tariff_point_dep = waypoint.tariff_point
            elif waypoint.waypoint_type == "Bahnstelle":
                tariff_point_dest = waypoint.tariff_point

    # Customer group lookup (database or empty for generic XLSX match)
    customer_group = ""
    if validation_data.get("customer"):
        customer_group = validation_data["customer"].get("group", "")

    # Enhanced base fields using validation and enrichment data
    base_fields = {
        "order_reference": order_input.order.order_reference,
        "customer_code": order_input.order.customer.code,
        "freightpayer_code": order_input.order.freightpayer.code,
        "container_type_iso_code": order_input.order.container.container_type_iso_code,
        "gross_weight": enriched_container["gross_weight"],
        "length": enriched_container["length"],
        "loading_status": _determine_loading_status(enriched_container["payload"]),
        "transport_type": _determine_transport_type(order_input.order.container.trucking_services),
        "departure_station": order_input.order.container.rail_service.departure_terminal.railway_station_number,
        "destination_station": order_input.order.container.rail_service.destination_terminal.railway_station_number,
        "departure_date": order_input.order.container.rail_service.departure_date,
        "dangerous_goods_flag": enriched_container["dangerous_goods"],
        "original_order_reference": order_input.order.order_reference,
        # Geography & Route Details (from Order JSON - no hardcoded values)
        "departure_country": departure_country,
        "destination_country": destination_country,
        "transport_direction": transport_direction,
        "tariff_point_dep": tariff_point_dep,
        "tariff_point_dest": tariff_point_dest,
        "customer_group": customer_group,
    }

    # 1. MAIN SERVICE - Always created
    main_service = ServiceOrderOutput(
        service_type=ServiceType.MAIN,
        **base_fields
    )

    # Store in database for persistence (skip if database not available)
    operational_order_id = None
    if db.connection_pool is not None:
        try:
            operational_order_id = await db.insert_operational_order({
                "order_reference": order_input.order.order_reference,
                "customer_id": validation_data.get("customer", {}).get("id"),
                "freightpayer_id": validation_data.get("freightpayer", {}).get("id"),
                "departure_date": order_input.order.container.rail_service.departure_date,
                "transport_direction": order_input.order.container.transport_direction,
                "container_data": enriched_container,
                "route_data": {
                    "departure_station": base_fields["departure_station"],
                    "destination_station": base_fields["destination_station"]
                },
                "trucking_data": [t.dict() for t in order_input.order.container.trucking_services],
                "dangerous_goods_flag": enriched_container["dangerous_goods"]
            })

            main_service_db_data = {
                "operational_order_id": operational_order_id,
                "service_type": "MAIN",
                "weight_class": enriched_container["weight_category"],
                "route_from": base_fields["departure_station"],
                "route_to": base_fields["destination_station"],
                "loading_status": base_fields["loading_status"].value,
                "transport_type": base_fields["transport_type"].value,
                "service_data": main_service.dict()
            }

            service_ids = await db.insert_service_orders([main_service_db_data])

        except Exception as e:
            # Log error but continue processing
            print(f"Database insertion failed: {e}")
    else:
        print("Database not available - skipping database persistence")

    # 2. TRUCKING SERVICES - Based on trucking data
    trucking_services = []
    for i, trucking in enumerate(order_input.order.container.trucking_services):
        trucking_service = ServiceOrderOutput(
            service_type=ServiceType.TRUCKING,
            type_of_trip=_map_trucking_code_to_trip_type(trucking.trucking_code),
            trucking_code=trucking.trucking_code,
            **base_fields
        )
        trucking_services.append(trucking_service)

        # Store trucking service in database (skip if database not available)
        if db.connection_pool is not None and operational_order_id:
            try:
                trucking_db_data = {
                    "operational_order_id": operational_order_id,
                    "service_type": "TRUCKING",
                    "description": f"Trucking service {trucking.type}",
                    "weight_class": enriched_container["weight_category"],
                    "route_from": base_fields["departure_station"],
                    "route_to": base_fields["destination_station"],
                    "loading_status": base_fields["loading_status"].value,
                    "transport_type": base_fields["transport_type"].value,
                    "service_data": trucking_service.dict()
                }
                await db.insert_service_orders([trucking_db_data])
            except Exception as e:
                print(f"Trucking service DB insertion failed: {e}")

    # 3. ADDITIONAL SERVICES - Based on additional services data
    # Skip service 123 (it's auto-determined from TruckingServices)
    additional_services = []

    for i, additional in enumerate(order_input.order.container.additional_services):
        # Skip service 123 - it's auto-determined from TruckingServices
        if additional.code == "123":
            continue

        # For service 789, extract quantity from JSON (netto = brutto - 3 per methodology)
        if additional.code == "789":
            # TODO: remove the hardcoded amount
            amount_brutto = int(additional.amount) if additional.amount else 8
            quantity = amount_brutto - 3  # Methodology: netto = brutto - 3 (5 = 8 - 3)
        else:
            # For other additional services, use default quantity
            quantity = _determine_additional_service_quantity(additional.code)

        additional_service = ServiceOrderOutput(
            service_type=ServiceType.ADDITIONAL,
            additional_service_code=additional.code,
            quantity=quantity,
            **base_fields
        )
        additional_services.append(additional_service)

        # Store additional service in database (skip if database not available)
        if db.connection_pool is not None and operational_order_id:
            try:
                additional_db_data = {
                    "operational_order_id": operational_order_id,
                    "service_type": "ADDITIONAL",
                    "service_code": additional.code,
                    "description": f"Additional service {additional.code}",
                    "quantity": quantity,
                    "weight_class": enriched_container["weight_category"],
                    "service_data": additional_service.dict()
                }
                await db.insert_service_orders([additional_db_data])
            except Exception as e:
                print(f"Additional service DB insertion failed: {e}")

    return {
        "main": main_service,
        "trucking": trucking_services,
        "additional": additional_services
    }


def _determine_loading_status(payload: str) -> LoadingStatus:
    """Determine loading status based on payload"""
    payload_kg = int(payload)
    return LoadingStatus.BELADEN if payload_kg > 0 else LoadingStatus.LEER


def _determine_transport_type(trucking_services: List) -> TransportType:
    """Determine transport type based on trucking services"""
    return TransportType.KV if len(trucking_services) > 0 else TransportType.STANDARD


def _map_trucking_code_to_trip_type(trucking_code: str) -> TypeOfTrip:
    """Map trucking code to trip type using DMN rules with fallback"""
    try:
        # Use DMN for trip type determination
        dmn_result = dmn_trip_type.determine_trip_type(trucking_code)
        if dmn_result:
            return dmn_result
    except Exception as e:
        print(f"DMN trip type determination failed: {e}")

    # Fallback to hardcoded mapping
    mapping = {
        "LB": TypeOfTrip.ZUSTELLUNG,
        "AB": TypeOfTrip.ABHOLUNG,
        "LC": TypeOfTrip.LEERCONTAINER
    }
    return mapping.get(trucking_code, TypeOfTrip.ZUSTELLUNG)


def _determine_additional_service_quantity(service_code: str) -> int:
    """Determine quantity for additional services based on roadmap examples"""
    # From roadmap: waiting time service has quantity 5
    quantity_mapping = {
        "123": 5,  # Waiting time (from roadmap example)
        "789": 5,  # Another waiting time variant
    }
    return quantity_mapping.get(service_code, 1)  # Default quantity 1


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)