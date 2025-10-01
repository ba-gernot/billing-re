#!/usr/bin/env python3
"""
Test the rating service /rate-xlsx endpoint
"""

import sys
from pathlib import Path

# Add services to path
sys.path.append(str(Path(__file__).parent / "services" / "rating"))

def test_xlsx_rating_logic():
    """Test the XLSX rating logic without starting the full service"""
    print("=" * 80)
    print("TEST: Rating Service XLSX Endpoint Logic")
    print("=" * 80)

    from xlsx_dmn_processor import XLSXDMNProcessor
    from xlsx_price_loader import XLSXPriceLoader

    # Initialize processors
    current_dir = Path(__file__).parent / "services" / "rating"
    xlsx_dmn_processor = XLSXDMNProcessor(current_dir / "dmn-rules")
    xlsx_price_loader = XLSXPriceLoader(current_dir / "price-tables")

    print("✅ Processors initialized")

    # Simulate a service order (simplified ServiceOrderInput)
    service_order = {
        'service_type': 'Hauptleistung Transport',
        'customer_code': '234567',
        'weight_class': '20B',
        'transport_type': 'KV',
        'dangerous_goods_flag': True,
        'departure_date': '2025-07-13 16:25:00',
        'departure_station': '80155283',
        'destination_station': '80137943',
        'loading_status': 'beladen',
        'additional_service_code': '123'
    }

    # Build order context
    order_context = {
        'service_type': service_order['service_type'],
        'loading_status': service_order['loading_status'],
        'transport_type': service_order['transport_type'],
        'dangerous_goods': service_order['dangerous_goods_flag'],
        'departure_station': service_order['departure_station'],
        'destination_station': service_order['destination_station'],
        'service_date': service_order['departure_date'].replace('-', '').replace(':', '').replace(' ', '')[:8]
    }

    print()
    print("Order Context:", order_context)
    print()

    # Step 1: Service determination
    print("Step 1: Service Determination")
    print("-" * 80)
    determined_services = xlsx_dmn_processor.evaluate_service_determination_full(order_context)
    print(f"✅ Services determined: {len(determined_services)}")
    for service in determined_services:
        print(f"   - Service {service['code']}: {service['name']}")

    # Add service 123
    if service_order['additional_service_code'] == '123':
        determined_services.append({'code': 123, 'name': 'Zustellung Export'})
        print(f"   + Service 123: Zustellung Export (from additional_service_code)")

    # Auto-determine service 789
    determined_services = xlsx_dmn_processor.determine_service_789_from_123(determined_services)
    has_789 = any(s['code'] == 789 for s in determined_services)
    if has_789:
        print(f"   ✅ Service 789 auto-determined")

    # Step 2: Pricing
    print()
    print("Step 2: Pricing")
    print("-" * 80)

    total_amount = 0.0
    services = []

    for service in determined_services:
        service_code = str(service['code'])

        if service_code == '111':  # Main service
            price_result = xlsx_price_loader.get_main_service_price_advanced(
                customer_code=service_order['customer_code'],
                customer_group='30',
                offer_number='',
                departure_country='DE',
                departure_station=service_order['departure_station'],
                tariff_point_dep='',
                destination_country='DE',
                destination_station=service_order['destination_station'],
                tariff_point_dest='',
                direction='Export',
                loading_status=service_order['loading_status'],
                transport_form=service_order['transport_type'],
                container_length='20',
                weight_class=service_order['weight_class'],
                service_date=service_order['departure_date']
            )

            if price_result:
                print(f"✅ Service {service_code} ({service['name']}): €{price_result['price']} (specificity: {price_result['specificity']})")
                total_amount += price_result['price']
                services.append({
                    'code': service_code,
                    'name': service['name'],
                    'price': price_result['price']
                })
        else:  # Additional service
            quantity = service.get('quantity_netto', 1)

            price_result = xlsx_price_loader.get_additional_service_price_advanced(
                service_code=service_code,
                customer_code=service_order['customer_code'],
                customer_group='30',
                departure_station=service_order['departure_station'],
                destination_station=service_order['destination_station'],
                loading_status=service_order['loading_status'],
                transport_form=service_order['transport_type'],
                container_length='20',
                service_date=service_order['departure_date'],
                quantity=quantity
            )

            if price_result:
                print(f"✅ Service {service_code} ({service['name']}): €{price_result['price_per_unit']} × {price_result['quantity']} = €{price_result['total_price']}")
                total_amount += price_result['total_price']
                services.append({
                    'code': service_code,
                    'name': service['name'],
                    'price': price_result['total_price']
                })

    print()
    print("=" * 80)
    print(f"TOTAL: €{total_amount}")
    print("=" * 80)

    expected_total = 383
    if abs(total_amount - expected_total) < 0.01:
        print()
        print("🎯 ✅ SUCCESS: Rating service logic produces €383!")
        print()
        print("Services breakdown:")
        for service in services:
            print(f"   - Service {service['code']}: {service['name']} = €{service['price']}")
        return True
    else:
        print()
        print(f"⚠️  Amount mismatch: got €{total_amount}, expected €{expected_total}")
        return False

def main():
    """Main entry point"""
    print("🚀 Testing Rating Service XLSX Endpoint")
    print()

    try:
        success = test_xlsx_rating_logic()

        print()
        print("=" * 80)
        if success:
            print("✅ RATING SERVICE READY FOR €383 CALCULATION!")
        else:
            print("⚠️  RATING SERVICE LOGIC NEEDS ADJUSTMENT")
        print("=" * 80)

        return success

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
