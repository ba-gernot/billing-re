from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from pydantic import BaseModel
import time
from datetime import datetime
from contextlib import asynccontextmanager

from database.connection import rating_db
from rules.dmn_service_determination import DMNServiceDetermination
from rules.dmn_weight_classification import DMNWeightClassification
from dmn import get_dmn_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await rating_db.initialize()

    # Initialize DMN components
    global dmn_service_determination, dmn_weight_classification, dmn_engine
    dmn_service_determination = DMNServiceDetermination()
    dmn_weight_classification = DMNWeightClassification()
    dmn_engine = get_dmn_engine()

    # Preload DMN rules
    dmn_engine.reload_all_rules()

    yield
    # Shutdown
    await rating_db.close()

# Global DMN components
dmn_service_determination = None
dmn_weight_classification = None
dmn_engine = None

app = FastAPI(
    title="Rating Service",
    description="Determines services and calculates prices for billing orders with database-driven rules",
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


class ServiceOrderInput(BaseModel):
    service_type: str
    customer_code: str
    weight_class: str
    transport_type: str
    dangerous_goods_flag: bool
    departure_date: str
    departure_station: Optional[str] = None
    destination_station: Optional[str] = None
    loading_status: Optional[str] = None
    additional_service_code: Optional[str] = None
    quantity: Optional[int] = 1


class PricingResult(BaseModel):
    service_code: str
    service_name: str
    description: str
    base_price: float
    calculated_amount: float
    currency: str = "EUR"
    offer_code: Optional[str] = None
    price_source: str  # "customer_specific", "fallback", "hardcoded"


class ServiceDeterminationResult(BaseModel):
    applicable_services: List[str]
    rules_applied: List[str]
    context: Dict


class RatingResult(BaseModel):
    order_reference: str
    customer_id: Optional[str] = None
    services: List[PricingResult]
    service_determination: ServiceDeterminationResult
    total_amount: float
    processing_time_ms: float
    warnings: List[str] = []


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "rating"}


@app.post("/rate", response_model=RatingResult)
async def rate_services(service_orders: List[ServiceOrderInput]):
    """
    Enhanced rating with database-driven rules and pricing

    Process:
    1. Apply database service determination rules (all 8 rules from roadmap)
    2. Multi-level pricing lookup (customer-specific → fallback → hardcoded)
    3. Calculate final amounts with business logic
    4. Return comprehensive pricing breakdown
    """
    start_time = time.time()
    warnings = []

    try:
        # Get customer information for pricing context
        customer_data = None
        customer_id = None
        if service_orders:
            customer_data = await rating_db.get_customer_by_code(service_orders[0].customer_code)
            if customer_data:
                customer_id = customer_data['id']
            else:
                warnings.append(f"Customer {service_orders[0].customer_code} not found in database")

        services = []
        total_amount = 0.0
        all_applicable_services = []
        rules_applied = []

        for service_order in service_orders:
            # Step 1: Determine applicable services using database rules
            service_context = {
                "service_type": service_order.service_type,
                "transport_type": service_order.transport_type,
                "dangerous_goods": service_order.dangerous_goods_flag,
                "departure_date": service_order.departure_date,
                "departure_station": service_order.departure_station,
                "loading_status": service_order.loading_status,
                "has_additional_services": bool(service_order.additional_service_code)
            }

            applicable_services = await rating_db.apply_service_determination_rules(service_context)
            all_applicable_services.extend(applicable_services)

            # Step 2: For each applicable service, determine pricing
            for service_code in applicable_services:
                pricing_result = await _calculate_service_pricing(
                    service_code,
                    service_order,
                    customer_id,
                    warnings
                )
                services.append(pricing_result)
                total_amount += pricing_result.calculated_amount

            # Step 3: Handle additional services if specified
            if service_order.additional_service_code:
                additional_pricing = await _calculate_additional_service_pricing(
                    service_order.additional_service_code,
                    service_order.quantity or 1,
                    warnings
                )
                services.append(additional_pricing)
                total_amount += additional_pricing.calculated_amount

        processing_time = (time.time() - start_time) * 1000

        # Create service determination result
        service_determination = ServiceDeterminationResult(
            applicable_services=list(set(all_applicable_services)),
            rules_applied=rules_applied,
            context=service_context if service_orders else {}
        )

        return RatingResult(
            order_reference="ORD20250617-00042",  # Should come from transformation service
            customer_id=customer_id,
            services=services,
            service_determination=service_determination,
            total_amount=total_amount,
            processing_time_ms=processing_time,
            warnings=warnings
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rating failed: {str(e)}")


async def _calculate_service_pricing(service_code: str, service_order: ServiceOrderInput,
                                     customer_id: Optional[str], warnings: List[str]) -> PricingResult:
    """Calculate pricing for a service using multi-level lookup strategy"""

    # Strategy: Customer-specific → Fallback → Hardcoded
    price_info = None
    price_source = "hardcoded"
    offer_code = None

    # Level 1: Customer-specific pricing
    if customer_id:
        price_info = await rating_db.get_customer_pricing(
            customer_id,
            service_order.weight_class,
            "Export"  # From transformation service context
        )
        if price_info:
            price_source = "customer_specific"
            offer_code = price_info.get("offer_code")

    # Level 2: Fallback pricing
    if not price_info:
        price_info = await rating_db.get_fallback_pricing(
            service_order.weight_class,
            "Export"
        )
        if price_info:
            price_source = "fallback"
            offer_code = price_info.get("offer_code")

    # Level 3: Hardcoded pricing (roadmap examples)
    if not price_info:
        hardcoded_prices = {
            "111": {"price": 100.0, "description": "Generic main service"},
            "222": {"price": 18.0, "description": "Trucking service - Zustellung"},
            "444": {"price": 85.0, "description": "Standard KV service"},
            "456": {"price": 15.0, "description": "Security service - KV dangerous"},
            "333": {"price": 25.0, "description": "Station security"},
            "555": {"price": 35.0, "description": "Customs documentation"},
            "789": {"price": 250.0, "description": "Waiting time (5 units × €50)"}
        }

        if service_code in hardcoded_prices:
            hardcoded = hardcoded_prices[service_code]
            price_info = {
                "price": hardcoded["price"],
                "minimum_price": hardcoded["price"],
                "currency": "EUR"
            }
        else:
            warnings.append(f"No pricing found for service code {service_code}, using default")
            price_info = {"price": 50.0, "minimum_price": 50.0, "currency": "EUR"}

    # Calculate final amount (apply minimum price rule)
    base_price = price_info["price"]
    minimum_price = price_info.get("minimum_price", base_price)
    calculated_amount = max(base_price, minimum_price)

    return PricingResult(
        service_code=service_code,
        service_name=f"Service {service_code}",
        description=_get_service_description(service_code),
        base_price=base_price,
        calculated_amount=calculated_amount,
        currency=price_info.get("currency", "EUR"),
        offer_code=offer_code,
        price_source=price_source
    )


async def _calculate_additional_service_pricing(service_code: str, quantity: int,
                                               warnings: List[str]) -> PricingResult:
    """Calculate pricing for additional services"""

    # Database lookup for additional service pricing
    price_info = await rating_db.get_additional_service_pricing(service_code)

    if price_info:
        base_price = price_info["price"]
        price_type = price_info["price_type"]

        if price_type == "per_unit":
            calculated_amount = base_price * quantity
        else:
            calculated_amount = base_price

        return PricingResult(
            service_code=service_code,
            service_name=price_info["service_name"],
            description=f"Additional service {service_code} (quantity: {quantity})",
            base_price=base_price,
            calculated_amount=calculated_amount,
            currency=price_info.get("currency", "EUR"),
            price_source="database"
        )
    else:
        # Fallback for additional services
        warnings.append(f"Additional service {service_code} not found in database, using hardcoded")
        base_price = 50.0  # Default additional service price
        calculated_amount = base_price * quantity

        return PricingResult(
            service_code=service_code,
            service_name=f"Additional Service {service_code}",
            description=f"Additional service {service_code} (quantity: {quantity})",
            base_price=base_price,
            calculated_amount=calculated_amount,
            currency="EUR",
            price_source="hardcoded"
        )


def _get_service_description(service_code: str) -> str:
    """Get human-readable description for service codes"""
    descriptions = {
        "111": "Generic main service",
        "222": "Trucking service - Zustellung",
        "333": "Station security service",
        "444": "Standard KV service",
        "456": "Security surcharge for KV dangerous goods",
        "555": "Customs documentation",
        "789": "Waiting time service"
    }
    return descriptions.get(service_code, f"Service {service_code}")


# Legacy functions (kept for backward compatibility)
def _determine_service_code(service_order: ServiceOrderInput) -> str:
    """Legacy service determination (replaced by database rules)"""
    if service_order.service_type == "MAIN":
        if service_order.transport_type == "KV" and service_order.dangerous_goods_flag:
            return "456"
        elif service_order.transport_type == "KV":
            return "444"
        else:
            return "111"
    elif service_order.service_type == "TRUCKING":
        return "222"
    else:
        return "789"


def _lookup_price(service_code: str, service_order: ServiceOrderInput) -> float:
    """Legacy price lookup (replaced by database pricing)"""
    price_table = {
        "111": 100.0, "222": 18.0, "444": 85.0,
        "456": 15.0, "789": 250.0
    }
    return price_table.get(service_code, 50.0)


# DMN Management Endpoints

@app.get("/dmn/rules")
async def list_dmn_rules():
    """List all available DMN rules"""
    try:
        available_rules = dmn_engine.list_available_rules()
        rule_info = {}

        for rule_name in available_rules:
            info = dmn_engine.get_rule_info(rule_name)
            if info:
                rule_info[rule_name] = info

        return {
            "total_rules": len(available_rules),
            "loaded_rules": len([r for r in rule_info.values() if r.get('loaded', False)]),
            "rules": rule_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list DMN rules: {str(e)}")


@app.post("/dmn/reload")
async def reload_dmn_rules():
    """Reload all DMN rules from files"""
    try:
        results = dmn_engine.reload_all_rules()
        successful = len([r for r in results.values() if r])
        total = len(results)

        return {
            "message": f"Reloaded {successful}/{total} DMN rules",
            "results": results,
            "success": successful == total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload DMN rules: {str(e)}")


@app.post("/dmn/reload/{rule_name}")
async def reload_specific_dmn_rule(rule_name: str):
    """Reload a specific DMN rule"""
    try:
        engine = dmn_engine.get_engine(rule_name, force_reload=True)
        if engine:
            return {
                "message": f"Successfully reloaded DMN rule: {rule_name}",
                "rule_name": rule_name,
                "success": True
            }
        else:
            raise HTTPException(status_code=404, detail=f"DMN rule not found: {rule_name}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload DMN rule {rule_name}: {str(e)}")


@app.delete("/dmn/cache")
async def clear_dmn_cache():
    """Clear DMN rule cache"""
    try:
        dmn_engine.clear_cache()
        return {"message": "DMN cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear DMN cache: {str(e)}")


@app.delete("/dmn/cache/{rule_name}")
async def clear_rule_cache(rule_name: str):
    """Clear cache for a specific DMN rule"""
    try:
        dmn_engine.clear_cache(rule_name)
        return {"message": f"Cache cleared for DMN rule: {rule_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache for rule {rule_name}: {str(e)}")


@app.post("/dmn/test")
async def test_dmn_rule(rule_name: str, input_data: Dict):
    """Test a DMN rule with custom input data"""
    try:
        result = dmn_engine.execute_rule(
            rule_name=rule_name,
            input_data=input_data,
            use_cache=False
        )

        return {
            "rule_name": rule_name,
            "input_data": input_data,
            "result": result,
            "success": result is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test DMN rule {rule_name}: {str(e)}")


@app.get("/dmn/status")
async def get_dmn_status():
    """Get overall DMN system status"""
    try:
        service_status = dmn_service_determination.get_rule_status()
        weight_status = dmn_weight_classification.get_rule_status()

        return {
            "dmn_engine_initialized": dmn_engine is not None,
            "cache_enabled": dmn_engine.redis_client is not None if dmn_engine else False,
            "service_determination": service_status,
            "weight_classification": weight_status,
            "available_rules": dmn_engine.list_available_rules() if dmn_engine else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DMN status: {str(e)}")


# Enhanced rating endpoint with DMN integration

@app.post("/rate-dmn", response_model=RatingResult)
async def rate_services_dmn(service_orders: List[ServiceOrderInput]):
    """
    Enhanced rating with DMN-based service determination and weight classification

    Process:
    1. Apply DMN service determination rules (dynamic from files)
    2. DMN weight classification (dynamic from files)
    3. Multi-level pricing lookup (customer-specific → fallback → hardcoded)
    4. Calculate final amounts with business logic
    5. Return comprehensive pricing breakdown
    """
    start_time = time.time()
    warnings = []

    try:
        # Get customer information for pricing context
        customer_data = None
        customer_id = None
        if service_orders:
            customer_data = await rating_db.get_customer_by_code(service_orders[0].customer_code)
            if customer_data:
                customer_id = customer_data['id']
            else:
                warnings.append(f"Customer {service_orders[0].customer_code} not found in database")

        services = []
        total_amount = 0.0
        all_applicable_services = []
        rules_applied = ["DMN-based service determination", "DMN-based weight classification"]

        for service_order in service_orders:
            # Step 1: DMN-based weight classification
            if hasattr(service_order, 'container_length') and hasattr(service_order, 'gross_weight'):
                weight_class = dmn_weight_classification.classify_weight(
                    container_length=getattr(service_order, 'container_length', '20'),
                    gross_weight=getattr(service_order, 'gross_weight', 20000)
                )
                service_order.weight_class = weight_class
                rules_applied.append(f"Weight classification: {weight_class}")

            # Step 2: Prepare order data for DMN service determination
            main_order = {
                'order_reference': getattr(service_order, 'order_reference', 'ORD-DMN-TEST'),
                'customer_code': service_order.customer_code,
                'transport_direction': getattr(service_order, 'transport_direction', 'Export'),
                'loading_status': service_order.loading_status or 'beladen',
                'type_of_transport': service_order.transport_type,
                'dangerous_goods': service_order.dangerous_goods_flag,
                'weight_class': service_order.weight_class,
                'gross_weight': getattr(service_order, 'gross_weight', 20000),
                'container_length': getattr(service_order, 'container_length', '20'),
                'departure_date': service_order.departure_date
            } if service_order.service_type == "MAIN" else {}

            trucking_orders = [{
                'order_reference': getattr(service_order, 'order_reference', 'ORD-DMN-TEST'),
                'trucking_code': getattr(service_order, 'trucking_code', 'LB'),
                'station': service_order.departure_station or service_order.destination_station,
                'trucking_type': getattr(service_order, 'trucking_type', 'Standard'),
                'date': service_order.departure_date
            }] if service_order.service_type == "TRUCKING" else []

            additional_orders = [{
                'order_reference': getattr(service_order, 'order_reference', 'ORD-DMN-TEST'),
                'service_code': service_order.additional_service_code,
                'quantity': service_order.quantity,
                'station': service_order.departure_station,
                'customs_type': getattr(service_order, 'customs_type', 'N1'),
                'country': getattr(service_order, 'country', 'DE'),
                'date': service_order.departure_date
            }] if service_order.service_type == "ADDITIONAL" and service_order.additional_service_code else []

            # Step 3: DMN-based service determination
            determined_services = dmn_service_determination.determine_services(
                main_order=main_order,
                trucking_orders=trucking_orders,
                additional_orders=additional_orders
            )

            # Step 4: For each determined service, calculate pricing
            for service in determined_services:
                applicable_services.append(service.service_code)
                all_applicable_services.append(service.service_code)

                pricing_result = await _calculate_service_pricing(
                    service.service_code,
                    service_order,
                    customer_id,
                    warnings
                )

                # Update pricing result with DMN metadata
                pricing_result.description += f" (DMN: {service.metadata.get('determined_by', 'unknown')})"
                services.append(pricing_result)
                total_amount += pricing_result.calculated_amount

                rules_applied.append(f"Service {service.service_code}: {service.metadata.get('determined_by', 'unknown')}")

        processing_time = (time.time() - start_time) * 1000

        # Create service determination result
        service_determination = ServiceDeterminationResult(
            applicable_services=list(set(all_applicable_services)),
            rules_applied=rules_applied,
            context={
                "dmn_enabled": True,
                "service_determination_method": "DMN",
                "weight_classification_method": "DMN",
                "fallback_available": True
            }
        )

        return RatingResult(
            order_reference="ORD20250617-00042",  # Should come from transformation service
            customer_id=customer_id,
            services=services,
            service_determination=service_determination,
            total_amount=total_amount,
            processing_time_ms=processing_time,
            warnings=warnings
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DMN-based rating failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3002)