#!/usr/bin/env python3
"""
Methodology Validation Script
==============================

Validates that the implementation follows the 8-step methodology
documented in docs/BILLING_CALCULATION_METHODOLOGY.md

Expected Result: €483 for test order 1_operative_Auftragsdaten.json

Usage:
    python3 validate_methodology.py

Prerequisites:
    - All services must be running (transformation, rating, billing)
    - XLSX files must be accessible in shared/rules/
"""

import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def print_step(step_num, description):
    """Print a step header"""
    print(f"\n{BOLD}{BLUE}[STEP {step_num}]{RESET} {description}")


def print_success(message):
    """Print success message"""
    print(f"  {GREEN}✓{RESET} {message}")


def print_error(message):
    """Print error message"""
    print(f"  {RED}✗{RESET} {message}")


def print_warning(message):
    """Print warning message"""
    print(f"  {YELLOW}⚠{RESET} {message}")


def validate_file_structure():
    """Validate that XLSX files exist and are accessible"""
    print_step("PRE", "Validating file structure")

    project_root = Path(__file__).parent
    shared_rules = project_root / "shared" / "rules"

    required_files = [
        "5_Regeln_Gewichtsklassen.xlsx",
        "3_Regeln_Fahrttyp.xlsx",
        "4_Regeln_Leistungsermittlung.xlsx",
        "6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx",
        "6_Preistabelle_Nebenleistungen.xlsx",
        "3_1_Regeln_Steuerberechnung.xlsx"
    ]

    all_exist = True
    for filename in required_files:
        file_path = shared_rules / filename
        if file_path.exists():
            print_success(f"{filename} exists")
        else:
            print_error(f"{filename} NOT FOUND at {file_path}")
            all_exist = False

    # Check symlinks
    rating_dmn_rules = project_root / "services" / "rating" / "dmn-rules"
    if rating_dmn_rules.exists() and rating_dmn_rules.is_symlink():
        print_success(f"Rating service symlink OK: {rating_dmn_rules}")
    else:
        print_error(f"Rating service symlink BROKEN: {rating_dmn_rules}")
        all_exist = False

    return all_exist


def validate_step_2_weight_classification():
    """Validate Step 2: Weight Classification"""
    print_step(2, "Weight Classification")

    try:
        from services.rating.xlsx_dmn_processor import XLSXDMNProcessor
        from pathlib import Path

        project_root = Path(__file__).parent
        processor = XLSXDMNProcessor(project_root / "shared" / "rules")

        # Test case from methodology: 20ft, 23 tons → 20B
        result = processor.evaluate_weight_class(
            container_length="20",
            gross_weight=23000,  # 23,000 kg
            preisraster="N"
        )

        if result == "20B":
            print_success(f"Weight classification: 20ft, 23,000kg → {result} ✓")
            return True
        else:
            print_error(f"Weight classification FAILED: Expected 20B, got {result}")
            return False

    except Exception as e:
        print_error(f"Weight classification error: {e}")
        return False


def validate_step_4_service_determination():
    """Validate Step 4: Service Determination"""
    print_step(4, "Service Determination (COLLECT Policy)")

    try:
        from services.rating.xlsx_dmn_processor import XLSXDMNProcessor
        from pathlib import Path

        project_root = Path(__file__).parent
        processor = XLSXDMNProcessor(project_root / "shared" / "rules")

        # Test service determination for MAIN service
        order_context = {
            'service_type': 'Hauptleistung Transport',
            'loading_status': 'beladen',
            'transport_type': 'KV',
            'dangerous_goods': True,
            'departure_station': '80155283',
            'destination_station': '80137943',
            'service_date': '20250713'
        }

        services = processor.evaluate_service_determination_full(order_context)
        service_codes = [s['code'] for s in services]

        # Expected services: 111, 222, 444, 456 (from methodology)
        expected = [111, 222, 444, 456]

        all_found = all(code in service_codes for code in expected)

        if all_found:
            print_success(f"Service determination: {service_codes}")
            print_success(f"All expected services found: {expected}")
            return True
        else:
            print_error(f"Service determination INCOMPLETE: Expected {expected}, got {service_codes}")
            return False

    except Exception as e:
        print_error(f"Service determination error: {e}")
        return False


def validate_step_46_service_789():
    """Validate Step 4.6: Auto-determination of Service 789"""
    print_step("4.6", "Service 789 Auto-Determination")

    try:
        from services.rating.xlsx_dmn_processor import XLSXDMNProcessor
        from pathlib import Path

        project_root = Path(__file__).parent
        processor = XLSXDMNProcessor(project_root / "shared" / "rules")

        # Test with service 123 present
        services = [
            {'code': 123, 'name': 'Zustellung Export'},
            {'code': 111, 'name': 'Main Service'}
        ]

        result = processor.determine_service_789_from_123(services)
        service_codes = [s['code'] for s in result]

        if 789 in service_codes:
            service_789 = next(s for s in result if s['code'] == 789)
            print_success(f"Service 789 auto-added from 123")
            print_success(f"Quantity: {service_789.get('quantity_netto', 'N/A')} units")
            return True
        else:
            print_error(f"Service 789 NOT auto-determined")
            return False

    except Exception as e:
        print_error(f"Service 789 auto-determination error: {e}")
        return False


def print_summary(results):
    """Print validation summary"""
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Validation Summary{RESET}")
    print(f"{'='*60}")

    passed = sum(results.values())
    total = len(results)

    for step, success in results.items():
        status = f"{GREEN}PASS{RESET}" if success else f"{RED}FAIL{RESET}"
        print(f"  {step}: {status}")

    print(f"\n{BOLD}Total: {passed}/{total} checks passed{RESET}")

    if passed == total:
        print(f"\n{GREEN}{BOLD}✓ All validation checks PASSED!{RESET}")
        return 0
    else:
        print(f"\n{RED}{BOLD}✗ Some validation checks FAILED{RESET}")
        return 1


def main():
    """Run all validation checks"""
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}Billing Calculation Methodology Validation{RESET}")
    print(f"{'='*60}\n")
    print("Expected Result: €483 for test order 1_operative_Auftragsdaten.json")
    print("Documentation: docs/BILLING_CALCULATION_METHODOLOGY.md\n")

    results = {}

    # Pre-validation
    results["File Structure"] = validate_file_structure()

    # Step 2: Weight Classification
    results["Step 2: Weight Classification"] = validate_step_2_weight_classification()

    # Step 4: Service Determination
    results["Step 4: Service Determination"] = validate_step_4_service_determination()

    # Step 4.6: Service 789 Auto-determination
    results["Step 4.6: Service 789"] = validate_step_46_service_789()

    # Print summary and exit
    return print_summary(results)


if __name__ == "__main__":
    sys.exit(main())
