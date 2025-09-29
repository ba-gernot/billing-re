#!/usr/bin/env python3
"""
Pricing Service - Calculates prices based on DMN rules and XLSX price tables
Integrates DMN rule results with dynamic pricing from XLSX files
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

from xlsx_price_loader import XLSXPriceLoader
from dmn.engine import get_dmn_engine

logger = logging.getLogger(__name__)


class PricingService:
    """
    Pricing service that combines DMN rules with XLSX price tables
    """

    def __init__(self, price_tables_dir: Path = None):
        # Initialize DMN engine
        self.dmn_engine = get_dmn_engine()

        # Initialize price loader
        if price_tables_dir is None:
            price_tables_dir = Path(__file__).parent.parent.parent / "shared" / "price-tables"

        self.price_loader = XLSXPriceLoader(price_tables_dir)
        logger.info(f"Pricing service initialized with price tables at {price_tables_dir}")

    def calculate_order_price(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complete order pricing

        Args:
            order_data: Order data with container details

        Returns:
            Pricing breakdown with subtotal, tax, and total
        """

        result = {
            'weight_class': None,
            'main_price': 0.0,
            'additional_services': [],
            'additional_total': 0.0,
            'subtotal': 0.0,
            'tax_rate': 0.0,
            'tax_amount': 0.0,
            'total': 0.0,
            'currency': 'EUR',
            'errors': []
        }

        try:
            # Step 1: Determine weight class using DMN rules
            weight_class_result = self.dmn_engine.execute_rule('weight_class', {
                'Preisraster': order_data.get('preisraster', 'N'),
                'Length': str(order_data.get('container_length', '20')),
                'GrossWeight': order_data.get('gross_weight', 0)
            }, use_cache=False)

            if not weight_class_result:
                result['errors'].append("Failed to determine weight class")
                return result

            weight_class = weight_class_result.get('WeightClass')
            result['weight_class'] = weight_class
            logger.info(f"Weight class: {weight_class}")

            # Step 2: Get main service price from XLSX
            main_price = self.price_loader.get_main_service_price(
                offer_code=order_data.get('offer_code', '123456'),
                weight_class=weight_class,
                direction=order_data.get('direction', 'Export')
            )

            if main_price is None:
                result['errors'].append(f"Main price not found for {weight_class} {order_data.get('direction')}")
                main_price = 0.0

            result['main_price'] = main_price
            logger.info(f"Main service price: €{main_price}")

            # Step 3: Determine applicable additional services using DMN rules
            service_result = self.dmn_engine.execute_rule('service_determination', {
                'TransportType': order_data.get('transport_type', 'KV'),
                'DangerousGood': order_data.get('dangerous_goods', False)
            }, use_cache=False)

            service_codes = []
            if service_result:
                service_codes = service_result.get('services', [])
            logger.info(f"Applicable services: {service_codes}")

            # Step 4: Get prices for additional services from XLSX
            container_length = str(order_data.get('container_length', '20'))

            for service_code in service_codes:
                service_price = self.price_loader.get_additional_service_price(
                    service_code=str(service_code),
                    container_length=container_length
                )

                if service_price is not None:
                    result['additional_services'].append({
                        'code': service_code,
                        'price': service_price
                    })
                    result['additional_total'] += service_price
                else:
                    # Service code not found in price tables, use 0
                    logger.warning(f"Service {service_code} not found in price tables, using €0")
                    result['additional_services'].append({
                        'code': service_code,
                        'price': 0.0
                    })

            # Step 5: Calculate subtotal
            result['subtotal'] = result['main_price'] + result['additional_total']

            # Step 6: Calculate tax (simplified - would use tax rules in production)
            direction = order_data.get('direction', 'Export')
            if direction == 'Export':
                result['tax_rate'] = 0.0  # Export: 0% VAT
            elif direction == 'Import':
                result['tax_rate'] = 0.0  # Import: Reverse charge (0% for calculation)
            else:
                result['tax_rate'] = 19.0  # Domestic: 19% VAT

            result['tax_amount'] = result['subtotal'] * (result['tax_rate'] / 100.0)

            # Step 7: Calculate total
            result['total'] = result['subtotal'] + result['tax_amount']

            logger.info(f"Pricing complete: Subtotal €{result['subtotal']}, Tax €{result['tax_amount']}, Total €{result['total']}")

        except Exception as e:
            logger.error(f"Error calculating order price: {e}", exc_info=True)
            result['errors'].append(f"Pricing calculation failed: {str(e)}")

        return result

    def get_price_breakdown(self, order_data: Dict[str, Any]) -> str:
        """Get human-readable price breakdown"""

        result = self.calculate_order_price(order_data)

        lines = []
        lines.append("=" * 70)
        lines.append("PRICE BREAKDOWN")
        lines.append("=" * 70)
        lines.append(f"Weight Class: {result['weight_class']}")
        lines.append(f"Main Service: €{result['main_price']:.2f}")
        lines.append("")
        lines.append("Additional Services:")

        for service in result['additional_services']:
            lines.append(f"  - Service {service['code']}: €{service['price']:.2f}")

        lines.append("")
        lines.append(f"Subtotal: €{result['subtotal']:.2f}")
        lines.append(f"Tax ({result['tax_rate']:.1f}%): €{result['tax_amount']:.2f}")
        lines.append(f"Total: €{result['total']:.2f} {result['currency']}")

        if result['errors']:
            lines.append("")
            lines.append("Errors:")
            for error in result['errors']:
                lines.append(f"  ⚠️  {error}")

        lines.append("=" * 70)

        return "\n".join(lines)

    def reload_prices(self, force: bool = True) -> Dict[str, bool]:
        """Reload price tables from XLSX files"""
        return self.price_loader.reload_prices(force=force)