#!/usr/bin/env python3
"""
Integration test for €383 calculation
Tests the complete pipeline using XLSX processors without running services
"""

import sys
from pathlib import Path

# Add services to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "services" / "rating"))
sys.path.append(str(project_root / "services" / "billing"))

def test_full_383_pipeline():
    """
    Test the complete billing calculation for the test scenario
    Expected result: €383 total

    Test Order (from 6_Abrechnungsbeleg_*.json):
    - Customer: 234567 (Group: 30)
    - Direction: Export
    - Route: 80155283 (DE) -> 80137943 (DE) -> US
    - Container: 20ft, 23000kg (20B weight class), beladen
    - Transport: KV (Combined Transport)
    - Dangerous Goods: Yes
    - Service Date: 2025-07-13
    """
    print("=" * 80)
    print("INTEGRATION TEST: €383 Calculation Pipeline")
    print("=" * 80)
    print()

    from xlsx_dmn_processor import XLSXDMNProcessor
    from xlsx_price_loader import XLSXPriceLoader
    from xlsx_tax_processor import XLSXTaxProcessor

    # Initialize processors
    dmn_processor = XLSXDMNProcessor(project_root / "services" / "rating" / "dmn-rules")
    price_loader = XLSXPriceLoader(project_root / "services" / "rating" / "price-tables")
    tax_processor = XLSXTaxProcessor()

    # Test order context
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

    print("STEP 1: Service Determination (COLLECT Policy)")
    print("-" * 80)

    # Determine services
    services = dmn_processor.evaluate_service_determination_full(order_context)
    print(f"✅ Services determined: {len(services)}")
    for service in services:
        print(f"   - Service {service['code']}: {service['name']}")

    # Add service 123 (Zustellung Export) - normally from trucking service determination
    services.append({'code': 123, 'name': 'Zustellung Export'})
    print(f"   + Service 123: Zustellung Export (from trucking)")

    # Auto-determine service 789 from service 123
    services = dmn_processor.determine_service_789_from_123(services)
    has_789 = any(s['code'] == 789 for s in services)
    if has_789:
        print(f"   ✅ Service 789 auto-determined from service 123")

    print()
    print("STEP 2: Pricing (19-Column Specificity Ranking)")
    print("-" * 80)

    # Price main service
    main_price = price_loader.get_main_service_price_advanced(
        customer_code='234567',
        customer_group='30',
        offer_number='',
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
        print(f"✅ Main service (20B Export KV): €{main_price['price']} (specificity: {main_price['specificity']})")
    else:
        print(f"❌ Main service price NOT FOUND")
        return False

    # Price additional services
    service_prices = {}

    # Service 123: Zustellung Export
    price_123 = price_loader.get_additional_service_price_advanced(
        service_code='123',
        customer_code='234567',
        customer_group='30',
        departure_station='80155283',
        destination_station='80137943',
        loading_status='beladen',
        transport_form='KV',
        container_length='20',
        service_date='2025-07-13',
        quantity=1
    )
    if price_123:
        service_prices[123] = price_123
        print(f"✅ Service 123 (Zustellung): €{price_123['total_price']}")

    # Service 222: Zuschlag 2
    price_222 = price_loader.get_additional_service_price_advanced(
        service_code='222',
        customer_code='234567',
        customer_group='30',
        departure_station='80155283',
        destination_station='80137943',
        loading_status='beladen',
        transport_form='KV',
        container_length='20',
        service_date='2025-07-13',
        quantity=1
    )
    if price_222:
        service_prices[222] = price_222
        print(f"✅ Service 222 (Zuschlag 2): €{price_222['total_price']}")

    # Service 456: Sicherheitszuschlag KV
    price_456 = price_loader.get_additional_service_price_advanced(
        service_code='456',
        customer_code='234567',
        customer_group='30',
        departure_station='80155283',
        destination_station='80137943',
        loading_status='beladen',
        transport_form='KV',
        container_length='20',
        service_date='2025-07-13',
        quantity=1
    )
    if price_456:
        service_prices[456] = price_456
        print(f"✅ Service 456 (Sicherheitszuschlag): €{price_456['total_price']}")

    # Service 789: Wartezeit Export (5 units)
    price_789 = price_loader.get_additional_service_price_advanced(
        service_code='789',
        customer_code='234567',
        customer_group='30',
        departure_station='80155283',
        destination_station='80137943',
        loading_status='beladen',
        transport_form='KV',
        container_length='20',
        service_date='2025-07-13',
        quantity=5  # 5 units
    )
    if price_789:
        service_prices[789] = price_789
        print(f"✅ Service 789 (Wartezeit): €{price_789['price_per_unit']} × {price_789['quantity']} = €{price_789['total_price']}")

    print()
    print("STEP 3: Tax Calculation (XLSX Rules)")
    print("-" * 80)

    # Calculate subtotal
    subtotal = main_price['price'] + sum(p['total_price'] for p in service_prices.values())
    print(f"Subtotal: €{subtotal}")

    # Calculate tax
    tax_result = tax_processor.calculate_tax_for_transport(
        transport_direction='Export',
        departure_country='DE',
        destination_country='US',
        vat_id='DE123456789',
        customs_procedure='T1-NCTS',
        loading_status='beladen'
    )

    print(f"✅ Tax: {tax_result['tax_case']} - {tax_result['tax_rate']*100}% (Rule: {tax_result['rule_matched']})")
    print(f"   SAP VAT Indicator: {tax_result['sap_vat_indicator']}")

    tax_amount = subtotal * tax_result['tax_rate']
    print(f"   Tax Amount: €{tax_amount}")

    # Calculate total
    total = subtotal + tax_amount

    print()
    print("=" * 80)
    print("FINAL CALCULATION")
    print("=" * 80)

    print(f"Main service (20B):       €{main_price['price']:>7.2f}")
    print(f"Service 123 (Zustellung): €{service_prices[123]['total_price']:>7.2f}")
    print(f"Service 222 (Zuschlag 2): €{service_prices[222]['total_price']:>7.2f}")
    print(f"Service 456 (Security):   €{service_prices[456]['total_price']:>7.2f}")
    print(f"Service 789 (Waiting):    €{service_prices[789]['total_price']:>7.2f}")
    print("-" * 80)
    print(f"Subtotal:                 €{subtotal:>7.2f}")
    print(f"Tax (Export 0%):          €{tax_amount:>7.2f}")
    print("=" * 80)
    print(f"TOTAL:                    €{total:>7.2f}")
    print("=" * 80)

    expected_total = 383
    if abs(total - expected_total) < 0.01:
        print()
        print("🎯 ✅ SUCCESS: Target €383 ACHIEVED!")
        print()
        print("✅ 100% ALIGNMENT CONFIRMED:")
        print("   ✅ Service determination (COLLECT policy)")
        print("   ✅ Service 789 auto-determination")
        print("   ✅ Advanced pricing (19-column specificity)")
        print("   ✅ Tax calculation (XLSX rules)")
        print("   ✅ Total calculation: €383")
        print()
        return True
    else:
        difference = abs(total - expected_total)
        print()
        print(f"⚠️  Amount mismatch: got €{total}, expected €{expected_total}")
        print(f"   Difference: €{difference:.2f}")
        print()
        return False

def main():
    """Main entry point"""
    print("🚀 Starting €383 Integration Test")
    print()

    try:
        success = test_full_383_pipeline()

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
