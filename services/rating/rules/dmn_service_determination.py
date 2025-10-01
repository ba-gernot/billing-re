"""
Dynamic service determination using DMN rules
Replaces hardcoded service determination logic
"""

from typing import Dict, List, Any, Optional
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

logger = logging.getLogger(__name__)

try:
    from dmn import get_dmn_engine
except ImportError:
    logger.warning("DMN engine not available, using fallback")
    get_dmn_engine = None

try:
    from models.service_orders import ServiceOrder, ServiceType
except ImportError:
    # Fallback if models don't exist
    ServiceOrder = dict
    ServiceType = str


class DMNServiceDetermination:
    """
    Service determination using DMN rules with fallback to database rules
    """

    def __init__(self):
        self.dmn_engine = get_dmn_engine()

    def determine_services(self, main_order: Dict[str, Any],
                          trucking_orders: List[Dict[str, Any]],
                          additional_orders: List[Dict[str, Any]]) -> List[ServiceOrder]:
        """
        Determine all services for the given orders using DMN rules

        Args:
            main_order: Main service order data
            trucking_orders: List of trucking order data
            additional_orders: List of additional service order data

        Returns:
            List of ServiceOrder objects with determined service codes
        """
        services = []

        # Process main service
        if main_order:
            main_services = self._determine_main_services(main_order)
            services.extend(main_services)

        # Process trucking services
        for trucking_order in trucking_orders:
            trucking_services = self._determine_trucking_services(trucking_order)
            services.extend(trucking_services)

        # Process additional services
        for additional_order in additional_orders:
            additional_services = self._determine_additional_services(additional_order)
            services.extend(additional_services)

        logger.info(f"Determined {len(services)} services using DMN rules")
        return services

    def _determine_main_services(self, main_order: Dict[str, Any]) -> List[ServiceOrder]:
        """Determine main services using DMN rules"""
        services = []

        # Prepare input data for DMN
        dmn_input = self._prepare_main_service_input(main_order)

        # Try DMN rule first: 3_Regeln_Leistungsermittlung
        service_codes = self._execute_service_determination_dmn(dmn_input, "main")

        if not service_codes:
            # Fallback to hardcoded logic
            service_codes = self._fallback_main_service_determination(main_order)

        # Create ServiceOrder objects
        for service_code in service_codes:
            service = ServiceOrder(
                service_type=ServiceType.MAIN,
                service_code=service_code,
                quantity=1,
                unit_price=0.0,  # Will be determined in pricing phase
                gross_weight=main_order.get('gross_weight', 0),
                weight_class=main_order.get('weight_class', ''),
                transport_direction=main_order.get('transport_direction', ''),
                loading_status=main_order.get('loading_status', ''),
                dangerous_goods=main_order.get('dangerous_goods', False),
                route_data=main_order.get('route_data', {}),
                metadata={
                    'determined_by': 'dmn' if service_codes else 'fallback',
                    'order_reference': main_order.get('order_reference'),
                    'customer_code': main_order.get('customer_code')
                }
            )
            services.append(service)

        return services

    def _determine_trucking_services(self, trucking_order: Dict[str, Any]) -> List[ServiceOrder]:
        """Determine trucking services using DMN rules"""
        services = []

        # Prepare input data for DMN
        dmn_input = self._prepare_trucking_service_input(trucking_order)

        # Try DMN rule first
        service_codes = self._execute_service_determination_dmn(dmn_input, "trucking")

        if not service_codes:
            # Fallback to hardcoded logic
            service_codes = self._fallback_trucking_service_determination(trucking_order)

        # Create ServiceOrder objects
        for service_code in service_codes:
            service = ServiceOrder(
                service_type=ServiceType.TRUCKING,
                service_code=service_code,
                quantity=1,
                unit_price=0.0,
                trucking_code=trucking_order.get('trucking_code', ''),
                station=trucking_order.get('station', ''),
                metadata={
                    'determined_by': 'dmn' if service_codes else 'fallback',
                    'order_reference': trucking_order.get('order_reference'),
                    'trucking_type': trucking_order.get('trucking_type', '')
                }
            )
            services.append(service)

        return services

    def _determine_additional_services(self, additional_order: Dict[str, Any]) -> List[ServiceOrder]:
        """Determine additional services using DMN rules"""
        services = []

        # Prepare input data for DMN
        dmn_input = self._prepare_additional_service_input(additional_order)

        # Try DMN rule first
        service_codes = self._execute_service_determination_dmn(dmn_input, "additional")

        if not service_codes:
            # Fallback to hardcoded logic
            service_codes = self._fallback_additional_service_determination(additional_order)

        # Create ServiceOrder objects
        for service_code in service_codes:
            service = ServiceOrder(
                service_type=ServiceType.ADDITIONAL,
                service_code=service_code,
                quantity=additional_order.get('quantity', 1),
                unit_price=0.0,
                additional_service_code=additional_order.get('service_code', ''),
                metadata={
                    'determined_by': 'dmn' if service_codes else 'fallback',
                    'order_reference': additional_order.get('order_reference'),
                    'original_service_code': additional_order.get('service_code', '')
                }
            )
            services.append(service)

        return services

    def _prepare_main_service_input(self, main_order: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input data for main service DMN rule"""
        return {
            'transportDirection': main_order.get('transport_direction', ''),
            'loadingStatus': main_order.get('loading_status', ''),
            'typeOfTransport': main_order.get('type_of_transport', ''),
            'dangerousGoods': main_order.get('dangerous_goods', False),
            'weightClass': main_order.get('weight_class', ''),
            'grossWeight': main_order.get('gross_weight', 0),
            'containerLength': main_order.get('container_length', ''),
            'currentDate': main_order.get('departure_date', ''),
            'customerCode': main_order.get('customer_code', ''),
            'orderType': 'MAIN'
        }

    def _prepare_trucking_service_input(self, trucking_order: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input data for trucking service DMN rule"""
        return {
            'truckingCode': trucking_order.get('trucking_code', ''),
            'station': trucking_order.get('station', ''),
            'truckingType': trucking_order.get('trucking_type', ''),
            'currentDate': trucking_order.get('date', ''),
            'orderType': 'TRUCKING'
        }

    def _prepare_additional_service_input(self, additional_order: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare input data for additional service DMN rule"""
        return {
            'serviceCode': additional_order.get('service_code', ''),
            'quantity': additional_order.get('quantity', 1),
            'station': additional_order.get('station', ''),
            'customsType': additional_order.get('customs_type', ''),
            'country': additional_order.get('country', ''),
            'currentDate': additional_order.get('date', ''),
            'orderType': 'ADDITIONAL'
        }

    def _execute_service_determination_dmn(self, dmn_input: Dict[str, Any],
                                         service_type: str) -> List[str]:
        """Execute DMN rule for service determination"""
        try:
            # Use the comprehensive service determination DMN
            result = self.dmn_engine.execute_rule(
                rule_name="3_Regeln_Leistungsermittlung",
                input_data=dmn_input,
                use_cache=True
            )

            if result and isinstance(result, dict):
                # Extract service codes from DMN result
                service_codes = []

                # Handle different DMN result formats
                if 'serviceCodes' in result:
                    service_codes = result['serviceCodes']
                elif 'serviceCode' in result:
                    service_codes = [result['serviceCode']]
                elif 'services' in result:
                    service_codes = [s.get('code') for s in result['services'] if s.get('code')]

                # Filter out None values
                service_codes = [code for code in service_codes if code]

                logger.debug(f"DMN service determination for {service_type}: {service_codes}")
                return service_codes

        except Exception as e:
            logger.warning(f"DMN service determination failed for {service_type}: {e}")

        return []

    def _fallback_main_service_determination(self, main_order: Dict[str, Any]) -> List[str]:
        """Fallback hardcoded main service determination"""
        services = []

        transport_direction = main_order.get('transport_direction', '')
        loading_status = main_order.get('loading_status', '')
        type_of_transport = main_order.get('type_of_transport', '')
        dangerous_goods = main_order.get('dangerous_goods', False)
        departure_date = main_order.get('departure_date', '')

        # Rule 1: KV + Dangerous + Date range -> 456 (Security surcharge)
        if (type_of_transport == 'KV' and dangerous_goods and
            self._is_date_in_range(departure_date, '2025-05-01', '2025-08-31')):
            services.append('456')

        # Rule 2: Main + Loaded + KV + Dangerous -> 456 (Alternative security)
        elif loading_status == 'beladen' and type_of_transport == 'KV' and dangerous_goods:
            services.append('456')

        # Rule 3: Main + KV -> 444 (KV service)
        if type_of_transport == 'KV':
            services.append('444')

        # Rule 4: Main + Any -> 111 (Generic main)
        services.append('111')

        return services

    def _fallback_trucking_service_determination(self, trucking_order: Dict[str, Any]) -> List[str]:
        """Fallback hardcoded trucking service determination"""
        services = []

        station = trucking_order.get('station', '')

        # Rule 5: Station security
        if station in ['80155283', '80137943']:
            services.append('333')

        # Rule 6: Generic trucking
        services.append('222')

        return services

    def _fallback_additional_service_determination(self, additional_order: Dict[str, Any]) -> List[str]:
        """Fallback hardcoded additional service determination"""
        services = []

        service_code = additional_order.get('service_code', '')
        customs_type = additional_order.get('customs_type', '')
        country = additional_order.get('country', '')

        # Rule 7: Customs N1 + DE -> 555 (Customs document)
        if customs_type == 'N1' and country == 'DE':
            services.append('555')

        # Rule 8: Additional Service exists -> 789 (Waiting time)
        if service_code:
            services.append('789')

        return services

    def _is_date_in_range(self, date_str: str, start_date: str, end_date: str) -> bool:
        """Check if date is within range"""
        try:
            from datetime import datetime
            date_obj = datetime.fromisoformat(date_str.split('T')[0])
            start_obj = datetime.fromisoformat(start_date)
            end_obj = datetime.fromisoformat(end_date)
            return start_obj <= date_obj <= end_obj
        except Exception:
            return False

    def reload_rules(self) -> Dict[str, bool]:
        """Reload all DMN rules"""
        return self.dmn_engine.reload_all_rules()

    def get_rule_status(self) -> Dict[str, Any]:
        """Get status of all DMN rules"""
        available_rules = self.dmn_engine.list_available_rules()
        rule_info = {}

        for rule_name in available_rules:
            info = self.dmn_engine.get_rule_info(rule_name)
            if info:
                rule_info[rule_name] = info

        return {
            'total_rules': len(available_rules),
            'loaded_rules': len([r for r in rule_info.values() if r.get('loaded', False)]),
            'rules': rule_info
        }