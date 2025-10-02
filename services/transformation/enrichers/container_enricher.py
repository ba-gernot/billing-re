from typing import Dict, Any, Optional
from models.operational_order import Container
from database.connection import db


class ContainerEnricher:
    """Enriches container data with calculated and derived fields using database lookups"""

    def __init__(self):
        # Fallback mappings if database lookup fails
        self.fallback_mappings = {
            "22G1": {"length_ft": 20, "max_gross_weight_kg": 23000},
            "42G1": {"length_ft": 40, "max_gross_weight_kg": 30000},
            "22R1": {"length_ft": 20, "max_gross_weight_kg": 23000},
            "42R1": {"length_ft": 40, "max_gross_weight_kg": 30000},
            "22T1": {"length_ft": 20, "max_gross_weight_kg": 23000},
            "22P1": {"length_ft": 20, "max_gross_weight_kg": 23000},
        }

    async def enrich(self, container: Container, validation_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Enrich container with calculated fields using database data or fallbacks"""

        # Calculate gross weight
        tare_weight = int(container.tare_weight)
        payload = int(container.payload)
        gross_weight = tare_weight + payload

        # Use validation data if available (from database lookup), otherwise try database
        container_info = None
        if validation_data and "container_type" in validation_data:
            container_info = validation_data["container_type"]
        else:
            # Fallback to database lookup
            container_info = await db.get_container_type(container.container_type_iso_code)

        # Final fallback to hardcoded mappings
        if not container_info:
            container_info = self.fallback_mappings.get(
                container.container_type_iso_code,
                {"length_ft": 20, "max_gross_weight_kg": 23000}  # Default fallback
            )

        # Container length (will be used by rating service for weight classification)
        length = str(container_info["length_ft"])
        # Weight category will be determined by rating service using XLSX FEEL expressions (Step 2)
        weight_category = None

        # Check dangerous goods
        dangerous_goods = container.dangerous_good_flag == "J"

        return {
            "gross_weight": gross_weight,
            "length": length,
            "weight_category": weight_category,
            "dangerous_goods": dangerous_goods,
            "payload": payload,
            "tare_weight": tare_weight,
            "max_gross_weight": container_info["max_gross_weight_kg"],
            "within_weight_limits": gross_weight <= container_info["max_gross_weight_kg"],
            "container_type_data": container_info
        }

    # Removed _determine_weight_category method - weight classification now handled by rating service
    # using XLSX FEEL expressions from 5_Regeln_Gewichtsklassen.xlsx (Methodology Step 2)