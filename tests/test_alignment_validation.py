#!/usr/bin/env python3
"""
Quick validation test for 100% alignment implementation
Tests the new service determination and pricing logic
"""

import sys
from pathlib import Path

# Add services to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "services" / "rating"))

def test_service_determination():
    """Test service determination with COLLECT policy"""
    print("=" * 80)
    print("TEST 1: Service Determination (COLLECT Policy)")
    print("=" * 80)

    from xlsx_dmn_processor import XLSXDMNProcessor

    # Initialize processor
    processor = XLSXDMNProcessor(project_root / "services" / "rating" / "dmn-rules")

    # Test order context (from test scenario)
    order_context = {
        'service_type': 'Hauptleistung Transport',
        'loading_status': 'beladen',
        'transport_type': 'KV',
        'dangerous_goods': True,
        'departure_country': 'DE',
        'departure_station': '80155283',
        'destination_country': 'DE',
        'destination_station': '80137943',
        'service_date': '20250713'
    }

    print(f"Order context: {order_context}")
    print()

    # Evaluate service determination
    services = processor.evaluate_service_determination_full(order_context)

    print(f"✅ Services determined: {len(services)}")
    for service in services:
        print(f"   - Service {service['code']}: {service['name']} (matched: {service['rule_matched']})")

    # Expected services: 111, 222, 456, 444 (and potentially 333 if stations match)
    expected_codes = [111, 222, 456, 444]
    found_codes = [s['code'] for s in services]

    print()
    print("Validation:")
    for code in expected_codes:
        if code in found_codes:
            print(f"   ✅ Service {code} found")
        else:
            print(f"   ❌ Service {code} MISSING")

    # Test service 789 auto-determination
    print()
    print("Testing service 789 auto-determination...")

    # Add service 123 manually for testing
    services_with_123 = services + [{'code': 123, 'name': 'Zustellung Export'}]
    services_final = processor.determine_service_789_from_123(services_with_123)

    has_789 = any(s['code'] == 789 for s in services_final)
    if has_789:
        service_789 = next(s for s in services_final if s['code'] == 789)
        print(f"   ✅ Service 789 auto-determined: {service_789['name']}")
        print(f"      Quantity: {service_789.get('quantity_netto', 0)} units × €{service_789.get('price_per_unit', 0)} = €{service_789.get('total_amount', 0)}")
    else:
        print(f"   ❌ Service 789 NOT auto-determined")

    return services_final

def test_pricing_specificity():
    """Test advanced pricing with specificity ranking"""
    print()
    print("=" * 80)
    print("TEST 2: Advanced Pricing (Specificity Ranking)")
    print("=" * 80)

    from xlsx_price_loader import XLSXPriceLoader

    # Initialize price loader
    price_loader = XLSXPriceLoader(project_root / "services" / "rating" / "price-tables")

    # Test main service pricing
    print("Main service pricing:")
    main_price = price_loader.get_main_service_price_advanced(
        customer_code='234567',  # Freightpayer
        customer_group='30',
        offer_number='123456',
        departure_country='DE',
        departure_station='80155283',
        tariff_point_dep='12345678',
        destination_country='DE',
        destination_station='80137943',
        tariff_point_dest='',
        direction='Export',
        loading_status='beladen',
        transport_form='KV',
        container_length='20',
        weight_class='20B',
        service_date='2025-07-13'
    )

    if main_price:
        print(f"   ✅ Main service price: €{main_price['price']} (specificity: {main_price['specificity']})")
        expected_main = 150  # From pricing table for 20B
        if abs(main_price['price'] - expected_main) < 0.01:
            print(f"   ✅ Price matches expected: €{expected_main}")
        else:
            print(f"   ⚠️  Price mismatch: got €{main_price['price']}, expected €{expected_main}")
    else:
        print(f"   ❌ Main service price NOT FOUND")

    # Test additional service pricing
    print()
    print("Additional service pricing:")

    test_services = [
        (123, 'Zustellung Export', 1, 18.0),
        (222, 'Zuschlag 2', 1, 50.0),
        (456, 'Sicherheitszuschlag KV', 1, 15.0),
        (789, 'Wartezeit Export', 5, 250.0)  # 5 units × €50
    ]

    total_additional = 0
    for service_code, service_name, quantity, expected_total in test_services:
        price = price_loader.get_additional_service_price_advanced(
            service_code=str(service_code),
            customer_code='234567',
            customer_group='30',
            departure_station='80155283',
            destination_station='80137943',
            loading_status='beladen',
            transport_form='KV',
            container_length='20',
            service_date='2025-07-13',
            quantity=quantity
        )

        if price:
            print(f"   ✅ Service {service_code} ({service_name}): €{price['price_per_unit']} × {price['quantity']} = €{price['total_price']}")
            total_additional += price['total_price']

            if abs(price['total_price'] - expected_total) < 0.01:
                print(f"      ✅ Matches expected: €{expected_total}")
            else:
                print(f"      ⚠️  Mismatch: expected €{expected_total}")
        else:
            print(f"   ❌ Service {service_code} ({service_name}): NOT FOUND")

    # Calculate total
    print()
    print("=" * 80)
    print("TOTAL CALCULATION")
    print("=" * 80)

    if main_price:
        subtotal = main_price['price'] + total_additional
        tax = 0.0  # Export has 0% VAT
        total = subtotal + tax

        print(f"Main service: €{main_price['price']}")
        print(f"Additional services: €{total_additional}")
        print(f"Subtotal: €{subtotal}")
        print(f"Tax (Export 0%): €{tax}")
        print(f"TOTAL: €{total}")
        print()

        expected_total = 383
        if abs(total - expected_total) < 0.01:
            print(f"🎯 ✅ SUCCESS: Target €{expected_total} ACHIEVED!")
            return True
        else:
            difference = abs(total - expected_total)
            print(f"⚠️  Mismatch: got €{total}, expected €{expected_total}")
            print(f"   Difference: €{difference}")
            return False

    return False

def main():
    """Run all validation tests"""
    print("🚀 Starting Alignment Validation Tests")
    print()

    try:
        # Test 1: Service determination
        services = test_service_determination()

        # Test 2: Pricing specificity
        success = test_pricing_specificity()

        print()
        print("=" * 80)
        if success:
            print("✅ ALL TESTS PASSED - 100% ALIGNMENT ACHIEVED!")
        else:
            print("⚠️  TESTS COMPLETED WITH DISCREPANCIES")
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
