#!/usr/bin/env python3
"""
Dynamic XLSX DMN Rule Processor
Direct processor for XLSX rule files from requirement documents
Alternative to pyDMNrules that works with the specific format of requirement docs
"""

import openpyxl
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import logging
import re

logger = logging.getLogger(__name__)

class XLSXDMNProcessor:
    """
    Direct XLSX DMN rule processor that can work with requirement document formats
    """

    def __init__(self, rules_dir: Path):
        self.rules_dir = Path(rules_dir)
        self._rule_cache: Dict[str, Dict] = {}
        self._file_mtimes: Dict[str, float] = {}  # Track file modification times

    def load_rule_file(self, file_name: str, force_reload: bool = False) -> Optional[Dict]:
        """Load and parse an XLSX rule file with automatic modification detection"""

        file_path = self.rules_dir / file_name

        if not file_path.exists():
            logger.warning(f"Rule file not found: {file_path}")
            return None

        # Check if file was modified since last load
        try:
            current_mtime = file_path.stat().st_mtime
        except Exception as e:
            logger.error(f"Failed to get file modification time for {file_name}: {e}")
            current_mtime = 0

        # Use cache if file hasn't been modified and not forcing reload
        if not force_reload and file_name in self._rule_cache:
            cached_mtime = self._file_mtimes.get(file_name, 0)
            if current_mtime <= cached_mtime:
                logger.debug(f"Using cached rules for {file_name}")
                return self._rule_cache[file_name]
            else:
                logger.info(f"File {file_name} modified (cached: {cached_mtime}, current: {current_mtime}), reloading")

        # Load file and cache with modification time
        try:
            wb = openpyxl.load_workbook(file_path)
            rule_data = self._parse_workbook(wb, file_name)
            self._rule_cache[file_name] = rule_data
            self._file_mtimes[file_name] = current_mtime
            logger.info(f"Loaded rules from {file_name} (mtime: {current_mtime})")
            return rule_data

        except Exception as e:
            logger.error(f"Failed to load rule file {file_name}: {e}")
            return None

    def _parse_workbook(self, wb: openpyxl.Workbook, file_name: str) -> Dict:
        """Parse a workbook and extract rule data"""

        rule_data = {
            'file_name': file_name,
            'sheets': {},
            'rules': []
        }

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheet_data = self._parse_sheet(sheet, sheet_name)
            rule_data['sheets'][sheet_name] = sheet_data

            # Extract rules from sheet
            if sheet_data['headers'] and sheet_data['rows']:
                rules = self._extract_rules_from_sheet(sheet_data, sheet_name)
                rule_data['rules'].extend(rules)

        return rule_data

    def _parse_sheet(self, sheet, sheet_name: str) -> Dict:
        """
        Parse a worksheet and extract structured data

        For DMN decision tables, the format is:
        - Row 1: Table name in A1
        - Row 2: Hit policy in A2, headers in B2, C2, etc.
        - Row 3+: Empty in col A, data in B3+, C3+, etc.

        For regular sheets (Glossary, Decision):
        - Row 1: Headers
        - Row 2+: Data
        """

        sheet_data = {
            'name': sheet_name,
            'headers': [],
            'rows': [],
            'max_row': sheet.max_row,
            'max_column': sheet.max_column,
            'is_dmn_table': False
        }

        if sheet.max_row < 1:
            return sheet_data

        # Check if this is a DMN decision table
        # DMN tables have a table name in A1 and hit policy in A2 (row 2, col 1)
        cell_a1 = sheet.cell(1, 1).value
        cell_a2 = sheet.cell(2, 1).value

        if cell_a2 and str(cell_a2).strip() in ['U', 'A', 'P', 'F', 'R', 'O', 'C', 'C+', 'C<', 'C>', 'C#']:
            # This is a DMN decision table
            sheet_data['is_dmn_table'] = True
            sheet_data['table_name'] = str(cell_a1).strip() if cell_a1 else sheet_name
            sheet_data['hit_policy'] = str(cell_a2).strip()

            # Get headers from row 2, starting from column 2
            headers = []
            for col in range(2, sheet.max_column + 1):
                cell_value = sheet.cell(2, col).value
                if cell_value is not None:
                    headers.append(str(cell_value).strip())
                else:
                    headers.append(f"Col_{col}")

            sheet_data['headers'] = headers

            # Get data rows starting from row 3, column 2
            for row in range(3, sheet.max_row + 1):
                row_data = []
                for col in range(2, sheet.max_column + 1):
                    cell_value = sheet.cell(row, col).value
                    if cell_value is not None:
                        # Clean quoted strings
                        value_str = str(cell_value).strip()
                        # Remove outer quotes if present
                        if value_str.startswith('"') and value_str.endswith('"'):
                            value_str = value_str[1:-1]
                        row_data.append(value_str)
                    else:
                        row_data.append("")

                # Skip empty rows
                if any(cell for cell in row_data if cell):
                    sheet_data['rows'].append(row_data)
        else:
            # Regular sheet format (Glossary, Decision, etc.)
            # Get headers from first row
            headers = []
            for col in range(1, sheet.max_column + 1):
                cell_value = sheet.cell(1, col).value
                if cell_value is not None:
                    headers.append(str(cell_value).strip())
                else:
                    headers.append(f"Col_{col}")

            sheet_data['headers'] = headers

            # Get data rows
            for row in range(2, sheet.max_row + 1):
                row_data = []
                for col in range(1, sheet.max_column + 1):
                    cell_value = sheet.cell(row, col).value
                    if cell_value is not None:
                        row_data.append(str(cell_value).strip())
                    else:
                        row_data.append("")

                # Skip empty rows
                if any(cell for cell in row_data if cell):
                    sheet_data['rows'].append(row_data)

        return sheet_data

    def _extract_rules_from_sheet(self, sheet_data: Dict, sheet_name: str) -> List[Dict]:
        """Extract rules from sheet data based on known patterns"""

        rules = []
        headers = sheet_data['headers']
        rows = sheet_data['rows']

        for i, row in enumerate(rows):
            rule = {
                'sheet': sheet_name,
                'rule_id': f"{sheet_name}_{i+1}",
                'conditions': {},
                'outputs': {},
                'raw_row': row
            }

            # Map row data to headers
            for j, header in enumerate(headers):
                if j < len(row):
                    value = row[j]
                    if value and value != '':
                        # Clean up quoted values
                        cleaned_value = value.strip('"')
                        rule['conditions'][header] = cleaned_value
                        rule['outputs'][header] = cleaned_value

            rules.append(rule)

        return rules

    def evaluate_trip_type(self, trucking_code: str, **kwargs) -> Optional[str]:
        """Evaluate trip type based on trucking code"""

        # Load trip type rules
        rule_data = self.load_rule_file("trip_type.dmn.xlsx")
        if not rule_data:
            logger.warning("Trip type rules not loaded")
            return None

        # Find matching rule
        for rule in rule_data['rules']:
            # Check different possible column names for trucking code
            trucking_code_fields = ['Trucking Code', 'TruckingCode', 'Trucking_Code']
            trip_type_fields = ['TypeOfTrip', 'Trip Type', 'Type Of Trip', 'Fahrttyp']

            for tc_field in trucking_code_fields:
                if tc_field in rule['conditions']:
                    rule_code = rule['conditions'][tc_field]
                    if rule_code == trucking_code:
                        # Return the trip type
                        for tt_field in trip_type_fields:
                            if tt_field in rule['outputs']:
                                result = rule['outputs'][tt_field]
                                logger.debug(f"Trip type: {trucking_code} -> {result}")
                                return result

        # Default fallback
        default_trip_type = "Zustellung"
        logger.debug(f"Trip type fallback: {trucking_code} -> {default_trip_type}")
        return default_trip_type

    def evaluate_weight_class(self, container_length: str, gross_weight: float, preisraster: str = "N", **kwargs) -> Optional[str]:
        """
        Evaluate weight class based on container length and gross weight

        Args:
            container_length: Container length ("20" or "40")
            gross_weight: Gross weight in kg
            preisraster: Price grid identifier (default "N")

        Returns:
            Weight classification (e.g., "20A", "20B", "40A", etc.)
        """

        # Load weight classification rules
        rule_data = self.load_rule_file("weight_class.dmn.xlsx")
        if not rule_data:
            logger.warning("Weight classification rules not loaded")
            return None

        # Convert weight from kg to tons for comparison
        gross_weight_tons = gross_weight / 1000.0

        # Find matching rule
        for rule in rule_data['rules']:
            # Check different possible column names
            preisraster_fields = ['Preisraster', 'Price Grid', 'Grid']
            length_fields = ['Länge', 'Laenge', 'Length', 'Container Length']
            weight_fields = ['Gewicht', 'Weight', 'GrossWeight', 'Gross Weight']
            class_fields = ['WeightClass', 'Weight Class', 'Gewichtsklasse', 'Classification']

            preisraster_match = True  # Default to true if not specified
            length_match = False
            weight_match = False

            # Check preisraster (if specified in rule)
            for pf in preisraster_fields:
                if pf in rule['conditions']:
                    rule_preisraster = rule['conditions'][pf].strip('"\'')
                    if rule_preisraster != '-' and rule_preisraster != '':
                        preisraster_match = (rule_preisraster == preisraster)
                    break

            # Check length condition
            for lf in length_fields:
                if lf in rule['conditions']:
                    rule_length = rule['conditions'][lf].strip('"\'')
                    if rule_length == container_length or rule_length == '-':
                        length_match = True
                        break

            # Check weight condition using FEEL expression evaluation
            for wf in weight_fields:
                if wf in rule['conditions']:
                    rule_weight = rule['conditions'][wf]
                    if self._evaluate_weight_condition(gross_weight_tons, rule_weight):
                        weight_match = True
                        break

            # If all conditions match, return the classification
            if preisraster_match and length_match and weight_match:
                for cf in class_fields:
                    if cf in rule['outputs']:
                        result = rule['outputs'][cf]
                        logger.info(f"Weight class: {container_length}ft, {gross_weight}kg ({gross_weight_tons}t) -> {result}")
                        return result

        # No matching rule found
        logger.warning(f"No matching weight class rule for: {container_length}ft, {gross_weight}kg")
        return None

    def _evaluate_weight_condition(self, actual_weight: float, rule_condition: str) -> bool:
        """
        Evaluate if an actual weight value matches a FEEL rule condition

        Args:
            actual_weight: The actual weight value (in tons)
            rule_condition: FEEL expression like "<=20", ">20", "[10..20]"

        Returns:
            True if the weight matches the condition
        """

        if rule_condition == '-' or rule_condition == '':
            return True

        rule_condition = rule_condition.strip()

        try:
            # Handle range expressions like "[10..20]", "]10..20]", "[10..20[", etc.
            if '..' in rule_condition:
                # Extract bracket types and values
                left_inclusive = rule_condition[0] == '['
                right_inclusive = rule_condition[-1] == ']'

                # Remove brackets and extract range values
                range_str = rule_condition.strip('[]')
                parts = range_str.split('..')
                if len(parts) != 2:
                    logger.warning(f"Invalid range expression: {rule_condition}")
                    return False

                lower = float(parts[0].strip())
                upper = float(parts[1].strip())

                # Check if weight is in range
                if left_inclusive and right_inclusive:
                    return lower <= actual_weight <= upper
                elif left_inclusive and not right_inclusive:
                    return lower <= actual_weight < upper
                elif not left_inclusive and right_inclusive:
                    return lower < actual_weight <= upper
                else:
                    return lower < actual_weight < upper

            # Handle comparison expressions
            elif rule_condition.startswith('<='):
                threshold = float(rule_condition[2:].strip())
                return actual_weight <= threshold

            elif rule_condition.startswith('>='):
                threshold = float(rule_condition[2:].strip())
                return actual_weight >= threshold

            elif rule_condition.startswith('<'):
                threshold = float(rule_condition[1:].strip())
                return actual_weight < threshold

            elif rule_condition.startswith('>'):
                threshold = float(rule_condition[1:].strip())
                return actual_weight > threshold

            elif rule_condition.startswith('='):
                threshold = float(rule_condition[1:].strip())
                return actual_weight == threshold

            # Try direct numeric comparison
            else:
                try:
                    threshold = float(rule_condition)
                    return actual_weight == threshold
                except ValueError:
                    logger.warning(f"Could not parse weight condition: {rule_condition}")
                    return False

        except (ValueError, IndexError) as e:
            logger.warning(f"Error evaluating weight condition '{rule_condition}' for weight {actual_weight}: {e}")
            return False

        return False

    def evaluate_service_determination(self, verkehrsform: str, gefahrgut: bool,
                                      gueltig_von: str = None, gueltig_bis: str = None,
                                      **kwargs) -> Optional[List[int]]:
        """Evaluate which additional services apply"""

        # Load service determination rules
        rule_data = self.load_rule_file("service_determination.dmn.xlsx")
        if not rule_data:
            logger.warning("Service determination rules not loaded")
            return None

        applicable_services = []

        # Find matching rules
        for rule in rule_data['rules']:
            # Check conditions
            verkehrsform_fields = ['Verkehrsform', 'Transport Type', 'TransportType']
            gefahrgut_fields = ['Gefahrgut', 'Dangerous Goods', 'DangerousGoods']
            service_fields = ['AdditionalServiceCode', 'Service Code', 'ServiceCode']

            verkehrsform_match = True  # Default to true
            gefahrgut_match = True     # Default to true

            # Check Verkehrsform
            for vf in verkehrsform_fields:
                if vf in rule['conditions']:
                    rule_verkehrsform = rule['conditions'][vf]
                    if rule_verkehrsform != '-' and rule_verkehrsform != '':
                        verkehrsform_match = (rule_verkehrsform == verkehrsform)
                    break

            # Check Gefahrgut
            for gf in gefahrgut_fields:
                if gf in rule['conditions']:
                    rule_gefahrgut = rule['conditions'][gf]
                    if rule_gefahrgut != '-' and rule_gefahrgut != '':
                        # Handle boolean conversion
                        rule_gefahrgut_bool = rule_gefahrgut.lower() in ['true', '1', 'yes']
                        gefahrgut_match = (rule_gefahrgut_bool == gefahrgut)
                    break

            # If conditions match, extract service code
            if verkehrsform_match and gefahrgut_match:
                for sf in service_fields:
                    if sf in rule['outputs']:
                        service_code = rule['outputs'][sf]
                        try:
                            service_int = int(service_code)
                            if service_int not in applicable_services:
                                applicable_services.append(service_int)
                        except ValueError:
                            pass

        logger.debug(f"Service determination: {verkehrsform}, {gefahrgut} -> {applicable_services}")
        return applicable_services

    def get_available_rules(self) -> List[str]:
        """Get list of available rule files"""
        if not self.rules_dir.exists():
            return []

        xlsx_files = []
        for file_path in self.rules_dir.glob("*.xlsx"):
            xlsx_files.append(file_path.name)

        return sorted(xlsx_files)

    def reload_rules(self, force: bool = True) -> Dict[str, bool]:
        """Reload all cached rules, optionally forcing reload regardless of modification time"""
        results = {}
        cached_files = list(self._rule_cache.keys())

        if force:
            # Clear all caches for force reload
            self._rule_cache.clear()
            self._file_mtimes.clear()
            logger.info(f"Force reloading {len(cached_files)} rule files")

        # Reload each file (will auto-detect modifications if not forced)
        for file_name in cached_files:
            rule_data = self.load_rule_file(file_name, force_reload=force)
            results[file_name] = rule_data is not None

        return results

    def get_rule_info(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a rule file"""
        file_path = self.rules_dir / file_name

        if not file_path.exists():
            return None

        rule_data = self.load_rule_file(file_name)

        return {
            'file_name': file_name,
            'path': str(file_path),
            'exists': True,
            'loaded': rule_data is not None,
            'sheets': list(rule_data['sheets'].keys()) if rule_data else [],
            'rules_count': len(rule_data['rules']) if rule_data else 0,
            'size': file_path.stat().st_size,
            'modified': file_path.stat().st_mtime
        }