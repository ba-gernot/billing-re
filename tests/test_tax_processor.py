#!/usr/bin/env python3
"""
Quick test for XLSX tax processor
"""

import sys
from pathlib import Path

# Add billing service to path
sys.path.append(str(Path(__file__).parent / "services" / "billing"))

from xlsx_tax_processor import XLSXTaxProcessor

def test_export_tax():
    """Test Export scenario - should be 0% VAT"""
    print("=" * 80)
    print("TEST 1: Export Tax Calculation (Expected: 0% VAT)")
    print("=" * 80)

    processor = XLSXTaxProcessor()

    result = processor.calculate_tax_for_transport(
        transport_direction='Export',
        departure_country='DE',
        destination_country='US',
        vat_id='DE123456789',
        customs_procedure='T1-NCTS',
        loading_status='beladen'
    )

    print(f"Result: {result}")
    print()

    if result['tax_rate'] == 0.0:
        print("✅ Export tax correctly calculated as 0%")
    else:
        print(f"❌ Export tax incorrect: {result['tax_rate']} (expected 0.0)")

    return result

def test_domestic_tax():
    """Test Domestic scenario - should be 19% VAT"""
    print("=" * 80)
    print("TEST 2: Domestic Tax Calculation (Expected: 19% VAT)")
    print("=" * 80)

    processor = XLSXTaxProcessor()

    result = processor.calculate_tax_for_transport(
        transport_direction='Domestic',
        departure_country='DE',
        destination_country='DE',
        vat_id=None,
        customs_procedure=None,
        loading_status='beladen'
    )

    print(f"Result: {result}")
    print()

    if result['tax_rate'] == 0.19:
        print("✅ Domestic tax correctly calculated as 19%")
    else:
        print(f"❌ Domestic tax incorrect: {result['tax_rate']} (expected 0.19)")

    return result

def test_import_tax():
    """Test Import scenario - should be reverse charge (0%)"""
    print("=" * 80)
    print("TEST 3: Import Tax Calculation (Expected: Reverse Charge 0%)")
    print("=" * 80)

    processor = XLSXTaxProcessor()

    result = processor.calculate_tax_for_transport(
        transport_direction='Import',
        departure_country='US',
        destination_country='DE',
        vat_id='DE987654321',
        customs_procedure='T1-NCTS',
        loading_status='beladen'
    )

    print(f"Result: {result}")
    print()

    if result['tax_rate'] == 0.0:
        print("✅ Import tax correctly calculated as 0% (reverse charge)")
    else:
        print(f"❌ Import tax incorrect: {result['tax_rate']} (expected 0.0)")

    return result

def main():
    """Run all tax calculation tests"""
    print("🚀 Starting Tax Processor Tests")
    print()

    try:
        export_result = test_export_tax()
        domestic_result = test_domestic_tax()
        import_result = test_import_tax()

        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Export: {export_result['tax_case']} - {export_result['tax_rate']*100}% (Rule: {export_result['rule_matched']})")
        print(f"Domestic: {domestic_result['tax_case']} - {domestic_result['tax_rate']*100}% (Rule: {domestic_result['rule_matched']})")
        print(f"Import: {import_result['tax_case']} - {import_result['tax_rate']*100}% (Rule: {import_result['rule_matched']})")
        print()

        all_correct = (
            export_result['tax_rate'] == 0.0 and
            domestic_result['tax_rate'] == 0.19 and
            import_result['tax_rate'] == 0.0
        )

        if all_correct:
            print("✅ ALL TAX TESTS PASSED!")
        else:
            print("⚠️  SOME TAX TESTS FAILED")

        print("=" * 80)

        return all_correct

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
