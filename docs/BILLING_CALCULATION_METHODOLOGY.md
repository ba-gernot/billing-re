# Billing Calculation Methodology

**Version:** 1.0
**Date:** 2025-10-02
**Purpose:** Step-by-step methodology for calculating the final total amount from an operational order JSON

---

## Overview

This document describes the complete methodology a program must follow to calculate the final invoice amount from an operational order JSON file, using the business rules and pricing tables stored in XLSX files under `shared/rules/`.

**Expected Result:** €483 for the test order `1_operative_Auftragsdaten.json`

---

## Input: Operational Order JSON

The input is a JSON file with the following structure:

```json
{
  "Order": {
    "OrderReference": "ORD20250617-00042",
    "Customer": {
      "Code": "123456",
      "Name": "Kunde Test"
    },
    "Container": {
      "TransportDirection": "Export",
      "ContainerTypeIsoCode": "22G1",
      "TareWeight": "2000",
      "Payload": "21000",
      "TakeOver": {
        "DepartureCountryIsoCode": "DE"
      },
      "HandOver": {
        "DestinationCountryIsoCode": "US"
      },
      "RailService": {
        "DepartureDate": "2025-07-13 16:25:00",
        "DepartureTerminal": {
          "RailwayStationNumber": "80155283"
        },
        "DestinationTerminal": {
          "RailwayStationNumber": "80137943"
        }
      },
      "TruckingServices": [{
        "TruckingCode": "LB"
      }],
      "AdditionalServices": [
        { "Code": "123" },
        { "Code": "789", "Amount": "8", "Unit": "Einheit" }
      ],
      "DangerousGoodFlag": "J"
    }
  }
}
```

---

## Code Examples for XLSX Parsing

This section provides Python code examples using `openpyxl` library to extract data from XLSX files.

### Installing Dependencies

```bash
pip install openpyxl
```

### Example: Reading Weight Classification Rules

```python
import openpyxl

def load_weight_classification_rules(file_path):
    """
    Load weight classification rules from XLSX file.

    Args:
        file_path: Path to 5_Regeln_Gewichtsklassen.xlsx

    Returns:
        List of rule dictionaries
    """
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    rules = []

    # Read headers (row 1)
    headers = []
    for col in range(1, ws.max_column + 1):
        val = ws.cell(1, col).value
        headers.append(str(val) if val else f'Col{col}')

    # Read data rows (starting from row 2)
    for row_idx in range(2, ws.max_row + 1):
        row_data = []
        for col in range(1, ws.max_column + 1):
            val = ws.cell(row_idx, col).value
            row_data.append(val)

        # Skip empty rows
        if any(row_data):
            rule = {
                'preisraster': str(row_data[0]).strip('"') if row_data[0] else None,
                'container_length': str(row_data[1]).strip('"') if row_data[1] else None,
                'weight_condition': str(row_data[2]) if row_data[2] else None,
                'weight_class': str(row_data[3]).strip('"') if row_data[3] else None
            }
            rules.append(rule)

    return rules

# Usage
rules = load_weight_classification_rules('shared/rules/5_Regeln_Gewichtsklassen.xlsx')
for rule in rules:
    print(f"Container {rule['container_length']}ft, Weight {rule['weight_condition']} → {rule['weight_class']}")

# Output:
# Container 20ft, Weight <= 20 → 20A
# Container 20ft, Weight > 20 → 20B
# Container 40ft, Weight <= 10 → 40A
# Container 40ft, Weight ]10..20] → 40B
# Container 40ft, Weight ]20..30] → 40C
# Container 40ft, Weight > 30 → 40D
```

### Example: Reading Service Determination Rules

```python
def load_service_determination_rules(file_path):
    """
    Load service determination rules from XLSX file.

    Args:
        file_path: Path to 4_Regeln_Leistungsermittlung.xlsx

    Returns:
        List of rule dictionaries
    """
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    rules = []

    # Read data rows (row 2 onwards, row 1 is headers)
    for row_idx in range(2, ws.max_row + 1):
        row = []
        for col in range(1, min(ws.max_column + 1, 14)):
            val = ws.cell(row_idx, col).value
            row.append(val)

        # Skip empty rows
        if not any(row):
            continue

        rule = {
            'service_type': str(row[0]).strip('"') if row[0] else None,
            'loading_status': str(row[1]).strip('"') if row[1] else None,
            'transport_form': str(row[2]).strip('"') if row[2] else None,
            'dangerous_goods': str(row[3]).lower() == 'true' if row[3] else None,
            'customs_procedure': str(row[4]).strip('"') if row[4] else None,
            'departure_country': str(row[5]).strip('"') if row[5] else None,
            'departure_station': str(row[6]).strip('"') if row[6] else None,
            'destination_country': str(row[7]).strip('"') if row[7] else None,
            'destination_station': str(row[8]).strip('"') if row[8] else None,
            'valid_from': int(row[9]) if row[9] else None,
            'valid_to': int(row[10]) if row[10] else None,
            'service_code': int(row[11]) if row[11] else None,
            'service_name': str(row[12]) if row[12] else None
        }
        rules.append(rule)

    return rules

# Usage
rules = load_service_determination_rules('shared/rules/4_Regeln_Leistungsermittlung.xlsx')
for rule in rules:
    print(f"Service {rule['service_code']}: {rule['service_name']} "
          f"(Loading: {rule['loading_status']}, Transport: {rule['transport_form']}, "
          f"Dangerous: {rule['dangerous_goods']})")

# Output example:
# Service 111: Zuschlag 1 (Loading: None, Transport: None, Dangerous: None)
# Service 222: Zuschlag 2 (Loading: None, Transport: None, Dangerous: None)
# Service 456: Sicherheitszuschlag KV (Loading: beladen, Transport: KV, Dangerous: True)
```

### Example: Reading Main Service Pricing

```python
def load_main_service_pricing(file_path):
    """
    Load main service pricing table from XLSX file.

    Args:
        file_path: Path to 6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx

    Returns:
        List of pricing dictionaries
    """
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    prices = []

    # Read data rows (row 2 onwards)
    for row_idx in range(2, ws.max_row + 1):
        row = []
        for col in range(1, min(ws.max_column + 1, 20)):
            val = ws.cell(row_idx, col).value
            row.append(val)

        # Skip empty rows
        if not any(row):
            continue

        price = {
            'offer_number': row[0],
            'customer_group': row[1],
            'customer_number': row[2],
            'departure_country': row[3],
            'departure_station': row[4],
            'tariff_point_dep': row[5],
            'destination_country': row[6],
            'destination_station': row[7],
            'tariff_point_dest': row[8],
            'direction': row[9],
            'loading_status': row[10],
            'transport_form': row[11],
            'price_grid': row[12],
            'container_length': row[13],
            'weight_class': row[14],
            'valid_from': int(row[15]) if row[15] else None,
            'valid_to': int(row[16]) if row[16] else None,
            'price': float(row[17]) if row[17] else None,
            'notes': row[18]
        }
        prices.append(price)

    return prices

# Usage
prices = load_main_service_pricing('shared/rules/6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx')
for price in prices[:5]:  # Show first 5
    print(f"Offer {price['offer_number']}, Weight Class {price['weight_class']}, "
          f"Direction {price['direction']}: €{price['price']}")

# Output example:
# Offer 123456, Weight Class 20A, Direction Export: €100
# Offer 123456, Weight Class 20B, Direction Export: €150
# Offer 123456, Weight Class 40A, Direction Export: €200
```

### Example: Reading Additional Service Pricing

```python
def load_additional_service_pricing(file_path):
    """
    Load additional service pricing table from XLSX file.

    Args:
        file_path: Path to 6_Preistabelle_Nebenleistungen.xlsx

    Returns:
        List of pricing dictionaries
    """
    wb = openpyxl.load_workbook(file_path)
    ws = wb.active

    prices = []

    # Read data rows (row 2 onwards)
    for row_idx in range(2, ws.max_row + 1):
        row = []
        for col in range(1, min(ws.max_column + 1, 21)):
            val = ws.cell(row_idx, col).value
            row.append(val)

        # Skip empty rows
        if not any(row):
            continue

        price = {
            'service_code': int(row[0]) if row[0] else None,
            'service_name': str(row[1]) if row[1] else None,
            'customer_number': row[2],
            'customer_group': row[3],
            'offer_number': row[4],
            'departure_country': row[5],
            'departure_station': row[6],
            'destination_country': row[7],
            'destination_station': row[8],
            'loading_status': row[9],
            'transport_form': row[10],
            'container_length': row[15],
            'valid_from': int(row[16]) if row[16] else None,
            'valid_to': int(row[17]) if row[17] else None,
            'price_basis': str(row[18]) if row[18] else None,  # "Container" or "Einheit"
            'price': float(row[19]) if row[19] else None
        }
        prices.append(price)

    return prices

# Usage - Find Service 222 pricing
prices = load_additional_service_pricing('shared/rules/6_Preistabelle_Nebenleistungen.xlsx')
service_222 = [p for p in prices if p['service_code'] == 222]

for price in service_222:
    print(f"Service {price['service_code']} ({price['service_name']}): "
          f"€{price['price']} per {price['price_basis']}")

# Output:
# Service 222 (Zuschlag 2): €50 per Container
# Service 222 (Zuschlag 2): €100 per Container
```

### Example: Complete XLSX Extraction Script

```python
import openpyxl
from pathlib import Path

class BillingRulesLoader:
    """Complete loader for all billing XLSX rules"""

    def __init__(self, rules_dir):
        self.rules_dir = Path(rules_dir)

    def load_all_rules(self):
        """Load all rule files"""
        return {
            'weight_classification': self._load_weight_rules(),
            'trip_type': self._load_trip_type_rules(),
            'service_determination': self._load_service_rules(),
            'main_pricing': self._load_main_pricing(),
            'additional_pricing': self._load_additional_pricing(),
            'tax_calculation': self._load_tax_rules()
        }

    def _load_weight_rules(self):
        file_path = self.rules_dir / '5_Regeln_Gewichtsklassen.xlsx'
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active

        rules = []
        for row_idx in range(2, ws.max_row + 1):
            row = [ws.cell(row_idx, col).value for col in range(1, 5)]
            if any(row):
                rules.append({
                    'preisraster': str(row[0]).strip('"') if row[0] else None,
                    'container_length': str(row[1]).strip('"') if row[1] else None,
                    'weight_condition': str(row[2]) if row[2] else None,
                    'weight_class': str(row[3]).strip('"') if row[3] else None
                })
        return rules

    def _load_trip_type_rules(self):
        file_path = self.rules_dir / '3_Regeln_Fahrttyp.xlsx'
        wb = openpyxl.load_workbook(file_path)
        ws = wb.active

        rules = []
        for row_idx in range(2, ws.max_row + 1):
            row = [ws.cell(row_idx, col).value for col in range(1, 5)]
            if any(row):
                rules.append({
                    'trucking_code': str(row[0]).strip('"') if row[0] else None,
                    'trip_type': str(row[1]).strip('"') if row[1] else None
                })
        return rules

    # Additional methods for other rule types...

# Usage
loader = BillingRulesLoader('shared/rules')
all_rules = loader.load_all_rules()

print(f"Loaded {len(all_rules['weight_classification'])} weight classification rules")
print(f"Loaded {len(all_rules['service_determination'])} service determination rules")
print(f"Loaded {len(all_rules['main_pricing'])} main pricing entries")
print(f"Loaded {len(all_rules['additional_pricing'])} additional pricing entries")
```

---

## Step 1: Extract Order Context

Extract the following information from the JSON:

### 1.1 Container Details
- **Container Length**: Extract from `ContainerTypeIsoCode` (first 2 digits)
  - Example: "22G1" → "20" (20ft container)
  - Example: "45G1" → "40" (40ft container)
- **Tare Weight**: `TareWeight` in kg
- **Payload**: `Payload` in kg
- **Gross Weight**: `TareWeight + Payload` in kg, convert to tons (÷ 1000)

### 1.2 Transport Details
- **Transport Direction**: `TransportDirection` (Export/Import/Domestic)
- **Departure Country**: `TakeOver.DepartureCountryIsoCode`
- **Destination Country**: `HandOver.DestinationCountryIsoCode`
- **Departure Station**: `RailService.DepartureTerminal.RailwayStationNumber`
- **Destination Station**: `RailService.DestinationTerminal.RailwayStationNumber`
- **Departure Date**: `RailService.DepartureDate` → Convert to YYYYMMDD format

### 1.3 Service Details
- **Loading Status**: Default "beladen" (loaded) unless specified otherwise
- **Transport Form**: Default "KV" (combined transport) for rail+truck
- **Dangerous Goods**: `DangerousGoodFlag` ("J" = true, "N" = false)
- **Trucking Code**: `TruckingServices[].TruckingCode`
- **Additional Services**: `AdditionalServices[].Code` and quantities

### 1.4 Customer Details
- **Customer Code**: `Customer.Code`
- **Freight Payer Code**: `Freightpayer.Code` (if different from customer)

---

## Step 2: Weight Classification

**Rule File:** `shared/rules/5_Regeln_Gewichtsklassen.xlsx`

### 2.1 Load Weight Classification Rules
Parse the XLSX file:
- **Column 1**: Preisraster (Price grid, usually "N")
- **Column 2**: Länge (Container length: "20" or "40")
- **Column 3**: Gewicht (Weight condition in FEEL syntax)
- **Column 4**: Gewichtsklasse (Weight class result)

### 2.2 Evaluate Weight Condition

For each rule row:
1. Match **Preisraster** (usually "N")
2. Match **Container Length** ("20" or "40")
3. Evaluate **Weight Condition** using FEEL expression logic:

**FEEL Expression Syntax:**
- `<= 20` → Gross weight in tons ≤ 20
- `> 20` → Gross weight in tons > 20
- `]10..20]` → 10 < weight ≤ 20 (left exclusive, right inclusive)
- `[10..20]` → 10 ≤ weight ≤ 20 (both inclusive)
- `]20..30]` → 20 < weight ≤ 30

### 2.3 Return Weight Class

Return the first matching **Gewichtsklasse** value (e.g., "20A", "20B", "40A", "40B", "40C", "40D")

**Example:**
- Container: 20ft, Gross Weight: 23 tons
- Rule: Preisraster="N", Länge="20", Gewicht="> 20" → **"20B"** ✅

---

## Step 3: Trip Type Determination

**Rule File:** `shared/rules/3_Regeln_Fahrttyp.xlsx`

### 3.1 Load Trip Type Rules
Parse the XLSX file:
- **Column 1**: Trucking Code
- **Column 2**: Fahrttyp (Trip Type: "Zustellung", "Abholung", etc.)

### 3.2 Match Trucking Code

Find the row where **Trucking Code** matches the order's trucking code.

**Example:**
- Trucking Code: "LB" → Trip Type: **"Zustellung"** (Delivery)

---

## Step 4: Service Determination

**Rule File:** `shared/rules/4_Regeln_Leistungsermittlung.xlsx`

### 4.1 Load Service Determination Rules
Parse the XLSX file:
- **Column 1**: Leistung (Service type, e.g., "Hauptleistung Transport")
- **Column 2**: Ladezustand (Loading status: "beladen", "leer")
- **Column 3**: Verkehrsform (Transport form: "KV", "KVS")
- **Column 4**: Gefahrgut vorhanden (Dangerous goods: true/false)
- **Column 5**: Zollverfahren (Customs procedure)
- **Column 6**: Land Bahnstelle Versand (Departure country)
- **Column 7**: Bahnstellennummer Versand (Departure station)
- **Column 8**: Land Bahnstelle Empfang (Destination country)
- **Column 9**: Bahnstellenummer Empfang (Destination station)
- **Column 10**: gültig von (Valid from date: YYYYMMDD)
- **Column 11**: gültig bis (Valid to date: YYYYMMDD)
- **Column 12**: NGB-Code (Service code output)
- **Column 13**: NGB-Name (Service name)

### 4.2 Matching Logic (COLLECT Hit Policy)

For each rule row, check if ALL conditions match:

**Wildcard Rules:**
- Empty/null cell = **matches anything** (wildcard)
- Value in quotes (e.g., `"beladen"`) = **exact match required**

**Matching Process:**
1. **Service Type**: Match if order is "Hauptleistung Transport"
2. **Loading Status**: Match if equals order's loading status OR null
3. **Transport Form**: Match if equals "KV" or "KVS" OR null
4. **Dangerous Goods**: Match if `true` and order has dangerous goods OR null
5. **Customs Procedure**: Match if equals order's procedure OR null
6. **Departure Country**: Match if equals order's departure country OR null
7. **Departure Station**: Match if equals order's station OR null
8. **Destination Country**: Match if equals order's destination country OR null
9. **Destination Station**: Match if equals order's station OR null
10. **Date Range**: Order date must be between `gültig von` and `gültig bis`

### 4.3 Collect All Matching Services

**IMPORTANT:** Multiple rules can match (COLLECT policy). Add ALL matching service codes to the list.

**Example Matches:**
- Service **111** (Zuschlag 1): Always matches all transport
- Service **222** (Zuschlag 2): Always matches all transport
- Service **444** (Zuschlag 3): Matches beladen + KV
- Service **456** (Sicherheitszuschlag): Matches beladen + KV + dangerous goods

### 4.4 Add Trucking Services

If the order has `TruckingServices`, add the corresponding service codes:
- Trip Type "Zustellung" → Service **123** (Zustellung Export)

### 4.5 Add Explicit Additional Services

Add any services explicitly listed in `AdditionalServices[]`:
- Service **789** (Wartezeit Export) with quantity

---

## Step 5: Main Service Pricing

**Pricing File:** `shared/rules/6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx`

### 5.1 Load Main Service Pricing Table
Parse the XLSX file (19 columns):
- **Column 1**: Angebotsnummer (Offer number)
- **Column 2**: Kundengruppe (Customer group)
- **Column 3**: Kundennummer (Customer number)
- **Column 4**: Land Bahnstelle Versand (Departure country)
- **Column 5**: Bahnstellennummer Versand (Departure station)
- **Column 6**: Tarifpunkt Versand (Tariff point departure)
- **Column 7**: Land Bahnstelle Empfang (Destination country)
- **Column 8**: Bahnstellennummer Empfang (Destination station)
- **Column 9**: Tarifpunkt Empfang (Tariff point destination)
- **Column 10**: Richtung (Direction: Export/Import/Domestic)
- **Column 11**: Ladezustand (Loading status)
- **Column 12**: Verkehrsform (Transport form)
- **Column 13**: Preisraster (Price grid)
- **Column 14**: Container Länge (Container length)
- **Column 15**: Gewichtsklasse (Weight class)
- **Column 16**: gültig von (Valid from: YYYYMMDD)
- **Column 17**: gültig bis (Valid to: YYYYMMDD)
- **Column 18**: Preis (Price in EUR)
- **Column 19**: Anmerkung (Notes)

### 5.2 Specificity-Based Matching

For each pricing row, calculate a **specificity score**:

**Mandatory Matches** (no points, but required):
- **Direction** must match (Column 10)
- **Weight Class** must match (Column 15)
- **Container Length** must match (Column 14)
- **Date Range** must include order date (Columns 16-17)

**Specificity Points** (higher = more specific):
- Customer Number match (Column 3): **+1000 points**
- Customer Group match (Column 2): **+100 points**
- Offer Number match (Column 1): **+50 points**
- Departure Station match (Column 5): **+10 points**
- Destination Station match (Column 8): **+10 points**
- Tariff Point Departure match (Column 6): **+5 points**
- Tariff Point Destination match (Column 9): **+5 points**
- Loading Status match (Column 11): **+2 points**
- Transport Form match (Column 12): **+2 points**

### 5.3 Select Best Match

1. Filter rows that meet ALL mandatory criteria
2. Calculate specificity score for each
3. Sort by specificity (highest first)
4. Select the **first row** (most specific match)
5. Return the **Preis** (Column 18)

**Example:**
- Customer: 123456 (offer number)
- Direction: Export
- Weight Class: 20B
- Stations: 80155283 → 80137943
- Container: 20ft
- Date: 20250713

**Match:** Row 3 → **Price: €150**

---

## Step 6: Additional Service Pricing

**Pricing File:** `shared/rules/6_Preistabelle_Nebenleistungen.xlsx`

### 6.1 Load Additional Service Pricing Table
Parse the XLSX file (20 columns):
- **Column 1**: NGB-Code (Service code)
- **Column 2**: NGB Name (Service name)
- **Column 3**: Kundennummer (Customer number)
- **Column 4**: Kundengruppe (Customer group)
- **Column 5**: Angebotsnummer (Offer number)
- **Column 6**: Land Bahnstelle Versand (Departure country)
- **Column 7**: Bahnstellennummer Versand (Departure station)
- **Column 8**: Land Bahnstelle Empfang (Destination country)
- **Column 9**: Bahnstellennummer Empfang (Destination station)
- **Column 10**: Ladezustand (Loading status)
- **Column 11**: Verkehrsform (Transport form)
- **Column 12-15**: Tariff point details
- **Column 16**: Container Länge (Container length)
- **Column 17**: gültig von (Valid from: YYYYMMDD)
- **Column 18**: gültig bis (Valid to: YYYYMMDD)
- **Column 19**: Preisbezug (Price basis: "Container" or "Einheit")
- **Column 20**: Preis (Price per unit/container)

### 6.2 Price Each Service

For each service code from Step 4:

1. **Filter** pricing rows where Column 1 = service code
2. Calculate **specificity score** (same logic as Step 5.2):
   - Customer Number match: +1000
   - Customer Group match: +100
   - Offer Number match: +50
   - Station matches: +10 each
   - Loading/Transport matches: +2 each

3. **Date validation**: Order date within valid range
4. Select **highest specificity** match
5. Extract **Price** (Column 20) and **Price Basis** (Column 19)

### 6.3 Calculate Service Amount

**If Price Basis = "Container":**
- Amount = Price (fixed per container)

**If Price Basis = "Einheit" (per unit):**
- Amount = Price × Quantity
- Quantity source:
  - From `AdditionalServices[].Amount` in JSON
  - Or default quantity (e.g., 5 units for Service 789)

**Example Calculations:**

**Service 123 (Zustellung Export):**
- Customer: 234567
- Stations: 80155283 → (any)
- Price Basis: Container
- **Price: €18**

**Service 222 (Zuschlag 2):**
- Customer: 234567
- Stations: 80155283 → 80137943
- Container: 20ft
- Price Basis: Container
- **Price: €50**

**Service 456 (Sicherheitszuschlag KV):**
- Customer Group: 30
- Stations: 80155283 → 80137943
- Container: 20ft
- Price Basis: Container
- **Price: €15**

**Service 789 (Wartezeit Export):**
- Generic rule (no customer)
- Price Basis: **Einheit** (per unit)
- Price per unit: €50
- Quantity: 5 units (netto, from business logic)
- **Total: 5 × €50 = €250**

---

## Step 7: Tax Calculation

**Rule File:** `shared/rules/3_1_Regeln_Steuerberechnung.xlsx`

### 7.1 Load Tax Calculation Rules
Parse the XLSX file:
- **Column 1**: Hauptleistung (Main service type)
- **Column 2**: Ladezustand (Loading status)
- **Column 3**: Versandort (Departure location: Inland/Ausland)
- **Column 4**: Empfangsort (Destination location: Inland/Ausland)
- **Column 5**: USt-ID (VAT ID)
- **Column 6**: USt-Land (VAT country)
- **Column 7**: Transportrichtung (Direction: Export/Import/Domestic)
- **Column 8**: Zoll-Verfahren (Customs procedure)
- **Column 10**: Umsatzsteuer setzen (Apply VAT: ja/nein)
- **Column 11**: Steuerfall setzen (Tax case reference)
- **Column 12**: Hinweis 1 darstellen (Display notice)
- **Column 13**: SAP USt-Kennzeichen (SAP VAT indicator)
- **Column 14**: Angabe Zentrale Meldung (Central notification)

### 7.2 Determine Location Types

- **Inland** = Germany (DE)
- **Ausland** = Any other country

### 7.3 Match Tax Rule

For each rule row, check if conditions match:
- Service Type: "Transport"
- Loading Status: from order
- Departure Location: "Inland" if DE, else "Ausland"
- Destination Location: "Inland" if DE, else "Ausland"
- Transport Direction: Export/Import/Domestic
- Customs Procedure: from order (if applicable)

**Wildcard handling:**
- Empty/null = matches anything
- "nicht relevant" = matches anything

### 7.4 Extract Tax Details

From the matching row:
- **Apply VAT**: Column 10 ("ja" = true, "nein" = false)
- **Tax Rate**:
  - If Apply VAT = true → **19%** (German standard rate)
  - If Apply VAT = false → **0%**
- **Tax Case**: Column 11 (e.g., "§ 4 Nr. 3a UStG" for Export)

**Example for Export (DE → US):**
- Departure: Inland (DE)
- Destination: Ausland (US)
- Direction: Export
- **Apply VAT: nein (false)**
- **Tax Rate: 0%**
- **Tax Case: § 4 Nr. 3a UStG**

---

## Step 8: Calculate Final Total

### 8.1 Sum All Service Amounts

```
Subtotal = Main Service Price
         + Sum of all Additional Service Prices
```

### 8.2 Apply Tax

```
Tax Amount = Subtotal × Tax Rate
```

### 8.3 Calculate Final Total

```
Final Total = Subtotal + Tax Amount
```

---

## Complete Example Calculation

**Order:** `1_operative_Auftragsdaten.json`

### Input Data:
- Container: 20ft, 23 tons
- Direction: Export (DE → US)
- Stations: 80155283 → 80137943
- Dangerous Goods: Yes
- Date: 20250713

### Step-by-Step:

**Step 2: Weight Classification**
- 20ft, 23 tons → **20B**

**Step 4: Service Determination**
- Service 111 ✓
- Service 222 ✓
- Service 444 ✓
- Service 456 ✓ (dangerous goods)
- Service 123 ✓ (trucking)
- Service 789 ✓ (from JSON)

**Step 5: Main Service Pricing**
- 20B Export → **€150**

**Step 6: Additional Service Pricing**
- Service 123: **€18**
- Service 222: **€50**
- Service 456: **€15**
- Service 789: **€250** (5 units × €50)
- Service 111: Not priced (no match in pricing table)
- Service 444: Not priced (no match in pricing table)

**Step 7: Tax Calculation**
- Export → **0%** VAT

**Step 8: Final Total**
```
Main Service:        €150
Service 123:          €18
Service 222:          €50
Service 456:          €15
Service 789:         €250
                    -----
Subtotal:            €483
VAT (0%):              €0
                    -----
FINAL TOTAL:         €483
```

---

## Important Implementation Notes

### Wildcard Handling
- Empty/null cells in rules = match anything
- Empty/null cells in pricing = no specificity bonus

### Date Format
- All dates in XLSX: **YYYYMMDD** (integer format)
- Convert order dates to this format for comparison

### Specificity Priority
- Always select the **most specific** price match
- Higher customer-level specificity beats station-level

### COLLECT Policy
- Service determination can return **multiple services**
- Do NOT stop at first match

### Price Basis
- "Container" = fixed price
- "Einheit" = multiply by quantity

### Missing Prices
- If a service is determined but has no pricing match, price = €0
- Log warning for missing prices

### FEEL Expression Evaluation
Implement proper FEEL syntax parser for weight conditions:
- Support: `<`, `>`, `<=`, `>=`, `=`
- Support: `[min..max]`, `]min..max]`, `[min..max[`, `]min..max[`
- Left bracket `[` = inclusive, `]` = exclusive
- Right bracket `]` = inclusive, `[` = exclusive

---

## Validation

The methodology should produce:
- **€483** for test order `1_operative_Auftragsdaten.json`
- 0% VAT for Export orders
- 19% VAT for Domestic orders (DE → DE)

---

## Files Reference

All XLSX files located in `shared/rules/`:
1. `5_Regeln_Gewichtsklassen.xlsx` - Weight classification
2. `3_Regeln_Fahrttyp.xlsx` - Trip type determination
3. `4_Regeln_Leistungsermittlung.xlsx` - Service determination
4. `6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx` - Main service pricing
5. `6_Preistabelle_Nebenleistungen.xlsx` - Additional service pricing
6. `3_1_Regeln_Steuerberechnung.xlsx` - Tax calculation

---

**End of Methodology Document**
