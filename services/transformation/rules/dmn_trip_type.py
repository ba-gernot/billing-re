"""
Dynamic trip type determination using DMN rules
Replaces hardcoded trip type logic in transformation service
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# We'll import the DMN engine from the rating service since it's shared
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'rating'))

from dmn import get_dmn_engine


class DMNTripTypeClassification:
    """
    Trip type classification using DMN rules with fallback to hardcoded logic
    """

    def __init__(self):
        self.dmn_engine = get_dmn_engine()

    def determine_trip_type(self, trucking_code: str, station: str = None,
                           transport_type: str = None) -> str:
        """
        Determine trip type based on trucking code using DMN rules

        Args:
            trucking_code: Trucking code (e.g., "LB", "AN", "AB")
            station: Optional station code
            transport_type: Optional transport type

        Returns:
            Trip type (e.g., "Zustellung", "Anlieferung", "Abholung")
        """
        # Prepare input data for DMN
        dmn_input = {
            'truckingCode': trucking_code,
            'station': station or '',
            'transportType': transport_type or 'Standard'
        }

        # Try DMN rule first: 3_Regeln_Fahrttyp
        trip_type = self._execute_trip_type_dmn(dmn_input)

        if not trip_type:
            # Fallback to hardcoded logic
            trip_type = self._fallback_trip_type_determination(trucking_code)

        logger.debug(f"Trip type determination: {trucking_code} -> {trip_type}")
        return trip_type

    def _execute_trip_type_dmn(self, dmn_input: Dict[str, Any]) -> Optional[str]:
        """Execute DMN rule for trip type determination"""
        try:
            result = self.dmn_engine.execute_rule(
                rule_name="3_Regeln_Fahrttyp",
                input_data=dmn_input,
                use_cache=True
            )

            if result and isinstance(result, dict):
                # Extract trip type from DMN result
                trip_type = None

                if 'tripType' in result:
                    trip_type = result['tripType']
                elif 'typeOfTrip' in result:
                    trip_type = result['typeOfTrip']
                elif 'fahrttyp' in result:
                    trip_type = result['fahrttyp']

                if trip_type:
                    logger.debug(f"DMN trip type result: {trip_type}")
                    return trip_type

        except Exception as e:
            logger.warning(f"DMN trip type determination failed: {e}")

        return None

    def _fallback_trip_type_determination(self, trucking_code: str) -> str:
        """
        Fallback hardcoded trip type determination logic
        Based on the roadmap: TruckingCode "LB" → "Zustellung"
        """
        trip_type_mapping = {
            'LB': 'Zustellung',      # Delivery
            'AN': 'Anlieferung',     # Inbound delivery
            'AB': 'Abholung',        # Pickup
            'ZU': 'Zustellung',      # Delivery (alternative)
            'VL': 'Vorladung',       # Pre-loading
            'NL': 'Nachladung',      # Post-loading
        }

        trip_type = trip_type_mapping.get(trucking_code, 'Zustellung')  # Default to delivery
        logger.debug(f"Fallback trip type: {trucking_code} -> {trip_type}")
        return trip_type

    def get_valid_trip_types(self) -> list:
        """Get list of valid trip types"""
        return [
            'Zustellung',
            'Anlieferung',
            'Abholung',
            'Vorladung',
            'Nachladung',
            'Direktfahrt',
            'Umladung'
        ]

    def get_valid_trucking_codes(self) -> Dict[str, str]:
        """Get mapping of valid trucking codes to trip types"""
        return {
            'LB': 'Zustellung',
            'AN': 'Anlieferung',
            'AB': 'Abholung',
            'ZU': 'Zustellung',
            'VL': 'Vorladung',
            'NL': 'Nachladung',
            'DF': 'Direktfahrt',
            'UL': 'Umladung'
        }

    def validate_trip_type(self, trip_type: str) -> bool:
        """Validate if trip type is valid"""
        return trip_type in self.get_valid_trip_types()

    def validate_trucking_code(self, trucking_code: str) -> bool:
        """Validate if trucking code is valid"""
        return trucking_code in self.get_valid_trucking_codes()

    def process_multiple_trucking_orders(self, trucking_orders: list) -> list:
        """
        Process multiple trucking orders to determine trip types

        Args:
            trucking_orders: List of trucking order dicts

        Returns:
            List of trucking orders with added 'trip_type' field
        """
        processed_orders = []

        for order in trucking_orders:
            trucking_code = order.get('trucking_code', '')
            station = order.get('station', '')
            transport_type = order.get('transport_type', '')

            trip_type = self.determine_trip_type(
                trucking_code=trucking_code,
                station=station,
                transport_type=transport_type
            )

            # Add trip type to order data
            processed_order = order.copy()
            processed_order['trip_type'] = trip_type
            processed_orders.append(processed_order)

        return processed_orders

    def reload_rules(self) -> Dict[str, bool]:
        """Reload trip type DMN rules"""
        return self.dmn_engine.reload_all_rules()

    def get_rule_status(self) -> Dict[str, Any]:
        """Get status of trip type DMN rule"""
        rule_info = self.dmn_engine.get_rule_info("3_Regeln_Fahrttyp")
        return {
            'rule_name': '3_Regeln_Fahrttyp',
            'available': rule_info is not None,
            'loaded': rule_info.get('loaded', False) if rule_info else False,
            'last_modified': rule_info.get('modified') if rule_info else None,
            'fallback_enabled': True,
            'supported_codes': list(self.get_valid_trucking_codes().keys())
        }