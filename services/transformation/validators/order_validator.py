from typing import List
from pydantic import BaseModel
from datetime import datetime
import re

from models.operational_order import OperationalOrderInput
from database.connection import db


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    enrichment_data: dict = {}


class OrderValidator:
    """Validates operational order input according to business rules from roadmap"""

    def __init__(self):
        # Valid transport directions
        self.valid_transport_directions = {"Export", "Import", "Domestic"}

        # Valid trucking codes (from roadmap examples)
        self.valid_trucking_codes = {"LB", "AB", "LC"}

        # Weight limits (from roadmap validation rules)
        self.tare_weight_range = (1000, 5000)  # kg
        self.max_gross_weights = {
            "20": 23000,  # 20ft containers
            "40": 30000   # 40ft containers
        }

    async def validate(self, order: OperationalOrderInput) -> ValidationResult:
        """Comprehensive validation with database lookups and business rules"""
        errors = []
        warnings = []
        enrichment_data = {}

        # 1. Validate order reference format (from roadmap validation rules)
        if not self._validate_order_reference(order.order.order_reference):
            errors.append(
                f"Invalid order reference format: {order.order.order_reference}. "
                "Expected: ORD[YYYYMMDD]-[00000]"
            )

        # 2. Validate and enrich customer data
        customer_data = await db.get_customer(order.order.customer.code)
        if not customer_data:
            errors.append(f"Customer code {order.order.customer.code} not found in database")
        else:
            enrichment_data["customer"] = customer_data

        # 3. Validate freightpayer (could be same as customer)
        freightpayer_data = await db.get_customer(order.order.freightpayer.code)
        if not freightpayer_data:
            errors.append(f"Freightpayer code {order.order.freightpayer.code} not found in database")
        else:
            enrichment_data["freightpayer"] = freightpayer_data

        # 4. Validate and enrich container type (database lookup)
        container_type = await db.get_container_type(order.order.container.container_type_iso_code)
        if not container_type:
            errors.append(
                f"Invalid container type: {order.order.container.container_type_iso_code}. "
                "Container type not found in database"
            )
        else:
            enrichment_data["container_type"] = container_type

        # 5. Validate transport direction
        if order.order.container.transport_direction not in self.valid_transport_directions:
            errors.append(
                f"Invalid transport direction: {order.order.container.transport_direction}. "
                f"Valid directions: {self.valid_transport_directions}"
            )

        # 6. Validate tare weight against container specs and business rules
        try:
            tare_weight = int(order.order.container.tare_weight)

            # Business rule: tare weight range validation
            if not (self.tare_weight_range[0] <= tare_weight <= self.tare_weight_range[1]):
                errors.append(
                    f"Tare weight {tare_weight} outside valid range "
                    f"({self.tare_weight_range[0]}-{self.tare_weight_range[1]} kg)"
                )

            # Cross-validate with container type if available
            if container_type and abs(tare_weight - container_type["tare_weight_kg"]) > 500:
                warnings.append(
                    f"Tare weight {tare_weight} differs significantly from "
                    f"container type standard {container_type['tare_weight_kg']} kg"
                )

        except ValueError:
            errors.append("Tare weight must be a valid integer")
            tare_weight = 0

        # 7. Validate payload and calculate gross weight
        try:
            payload = int(order.order.container.payload)
            if payload < 0:
                errors.append("Payload cannot be negative")

            # Calculate gross weight and validate against container limits
            gross_weight = tare_weight + payload
            enrichment_data["gross_weight"] = gross_weight

            if container_type:
                max_gross = container_type["max_gross_weight_kg"]
                if gross_weight > max_gross:
                    errors.append(
                        f"Gross weight {gross_weight} kg exceeds container limit {max_gross} kg"
                    )

                # Determine weight class (from roadmap business rules)
                length = str(container_type["length_ft"])
                weight_class = self._determine_weight_class(length, gross_weight)
                enrichment_data["weight_class"] = weight_class
                enrichment_data["container_length"] = length

        except ValueError:
            errors.append("Payload must be a valid integer")

        # 8. Validate dates with business rules
        departure_date = order.order.container.rail_service.departure_date
        current_time = datetime.utcnow()

        if departure_date < current_time:
            warnings.append("Departure date is in the past")

        # Validate departure is before arrival if arrival date exists
        # (Note: arrival date not in current model, but good practice)

        # 9. Validate dangerous goods flag
        if order.order.container.dangerous_good_flag not in ["J", "N"]:
            errors.append("Dangerous goods flag must be 'J' or 'N'")

        enrichment_data["dangerous_goods"] = order.order.container.dangerous_good_flag == "J"

        # 10. Validate railway stations (should exist in station master data)
        departure_station = order.order.container.rail_service.departure_terminal.railway_station_number
        destination_station = order.order.container.rail_service.destination_terminal.railway_station_number

        if not departure_station:
            errors.append("Departure railway station number is required")

        if not destination_station:
            errors.append("Destination railway station number is required")

        if departure_station == destination_station:
            errors.append("Departure and destination stations cannot be the same")

        # 11. Validate trucking services with business rules
        if not order.order.container.trucking_services:
            warnings.append("No trucking services specified - will use Standard transport type")
        else:
            for i, trucking in enumerate(order.order.container.trucking_services):
                if not trucking.trucking_code:
                    errors.append(f"Trucking service {i+1} missing trucking code")
                elif trucking.trucking_code not in self.valid_trucking_codes:
                    errors.append(
                        f"Invalid trucking code {trucking.trucking_code}. "
                        f"Valid codes: {self.valid_trucking_codes}"
                    )

                if not trucking.waypoints:
                    errors.append(f"Trucking service {i+1} has no waypoints")
                else:
                    # Validate waypoint sequence
                    main_waypoints = [w for w in trucking.waypoints if w.is_main_address == "J"]
                    if len(main_waypoints) != 1:
                        errors.append(f"Trucking service {i+1} must have exactly one main waypoint")

        # 12. Additional Services validation
        if order.order.container.additional_services:
            for i, additional in enumerate(order.order.container.additional_services):
                if not additional.code:
                    errors.append(f"Additional service {i+1} missing service code")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            enrichment_data=enrichment_data
        )

    def _validate_order_reference(self, order_ref: str) -> bool:
        """Validate order reference format: ORD[YYYYMMDD]-[00000]"""
        pattern = r'^ORD\d{8}-\d{5}$'
        return bool(re.match(pattern, order_ref))

    def _determine_weight_class(self, length: str, gross_weight: int) -> str:
        """Determine weight class based on roadmap business rules (Section 4)"""
        if length == "20":
            return "20A" if gross_weight <= 20000 else "20B"
        elif length == "40":
            return "40A" if gross_weight <= 25000 else "40B"
        else:
            return "20A"  # Default fallback