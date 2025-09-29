# Pricing Storage Documentation

**Date**: 2025-09-29
**Status**: ✅ XLSX-Based Dynamic Pricing Implemented

---

## Overview

Prices are stored in **XLSX files** under `shared/price-tables/` for easy editing without code deployment, similar to DMN rules.

---

## File Locations

### Price Tables Directory
```
billing-re/shared/price-tables/
├── main_service_prices.xlsx          # Main rail service prices
└── additional_service_prices.xlsx    # Additional/trucking services
```

### Source Files (Requirement Documents)
```
Requirement documents/
├── 5_Preistabelle_Hauptleistungen_Einzelpreise.xlsx
└── 5_Preistabelle_Nebenleistungen.xlsx
```

---

## Price Table Structure

### Main Service Prices (`main_service_prices.xlsx`)

**Columns**:
- `Angebotsnummer` - Offer/customer code
- `Kundennummer` - Customer number
- `Land Bahnstelle Versand` - Departure country
- `Bahnstellen-nummer Versand` - Departure station number
- `Tarifpunkt Versand` - Departure tariff point
- `Land Bahnstelle Empfang` - Destination country
- `Bahnstellen-nummer Empfang` - Destination station number
- `Tarifpunkt Empfang` - Destination tariff point
- `Richtung` - Direction (Export/Import/Domestic)
- `Ladezustand` - Loading status (beladen/leer)
- `Verkehrsform` - Transport type (KV, etc.)
- `Preisraster` - Price grid (N, etc.)
- `Container Länge` - Container length (20/40)
- `Gewichts-klasse` - Weight class (20A, 20B, 40A-40D)
- **`Preis`** - **Price in EUR**
- `gültig von` - Valid from date (YYYYMMDD)
- `gültig bis` - Valid to date (YYYYMMDD)
- `Anmerkung` - Notes/comments

**Example Data**:
```
Offer: 123456
Weight Class: 20B
Direction: Export
Price: €150
```

### Additional Service Prices (`additional_service_prices.xlsx`)

**Columns**:
- `Code` - Service code (123, 456, etc.)
- `Name` - Service name/description
- `Kundennummer` - Customer number (or "alle" for all)
- `Land Bahnstelle Versand` - Departure country
- `Bahnstellen-nummer Versand` - Departure station number
- `Land Bahnstelle Empfang` - Destination country
- `Bahnstellen-nummer Empfang` - Destination station number
- `Ladezustand` - Loading status
- `Verkehrsform` - Transport type
- `Container Länge` - Container size (20/40) for size-dependent pricing
- **`Preis`** - **Price in EUR**
- `gültig von` - Valid from date (YYYYMMDD)
- `gültig bis` - Valid to date (YYYYMMDD)
- `Anmerkung` - Notes/comments

**Example Data**:
```
Code: 123
Name: Zustellung Export
Container: 20ft
Price: €18

Code: 456
Name: Sicherheitszuschlag KV
Container: 20ft
Price: €15
```

---

## Service Codes from Requirement Documents

Based on the original XLSX files, only these services are defined:

| Code | Name | Container 20ft | Container 40ft |
|------|------|----------------|----------------|
| 123 | Zustellung Export | €18 | €36 |
| 456 | Sicherheitszuschlag KV | €15 | €30 |

**Note**: Other service codes (111, 222, 333, 444, 555, 789) that appear in DMN service determination rules are **not defined** in the requirement documents. These may be:
- Future services to be added
- Placeholder codes
- Services with €0 price (included in main service)
- Services that need to be defined in the XLSX files

---

## Usage

### Automatic Loading

Prices are automatically loaded from XLSX files with modification detection:

```python
from pricing_service import PricingService

# Initialize service
pricing_service = PricingService()

# Calculate order pricing
order_data = {
    'offer_code': '123456',
    'container_length': '20',
    'gross_weight': 23000,
    'direction': 'Export',
    'transport_type': 'KV',
    'dangerous_goods': False
}

result = pricing_service.calculate_order_price(order_data)
print(f"Total: €{result['total']}")
```

### Manual Price Lookup

```python
from xlsx_price_loader import XLSXPriceLoader
from pathlib import Path

loader = XLSXPriceLoader(Path('shared/price-tables'))

# Get main service price
price = loader.get_main_service_price(
    offer_code='123456',
    weight_class='20B',
    direction='Export'
)
# Returns: 150.0

# Get additional service price
price = loader.get_additional_service_price(
    service_code='123',
    container_length='20'
)
# Returns: 18.0
```

### Updating Prices

✅ **To update prices, simply edit the XLSX files**:

1. Open `shared/price-tables/main_service_prices.xlsx` or `additional_service_prices.xlsx`
2. Edit the `Preis` column
3. Save the file
4. **Changes are detected automatically** on next API call (no restart needed)

**File Modification Detection**: The system tracks file modification times and automatically reloads prices when XLSX files change.

---

## Current Pricing Example (Test Scenario)

**Order**: ORD20250617-00042
- Container: 20ft, 23000kg → Weight Class **20B**
- Direction: **Export**
- Transport: KV
- Dangerous Goods: No

**Pricing Breakdown**:
```
Main Service (20B Export):     €150
Service 123 (Zustellung 20ft):  €18
Service 456 (Security 20ft):    €15
-----------------------------------
Subtotal:                      €183
Tax (Export 0%):                 €0
-----------------------------------
Total:                         €183
```

**Note**: The previous €383 target included additional services (111, 222, 333, 555, 789) that are not defined in the requirement documents. The actual total based on documented prices is **€183**.

---

## Architecture

### Components

1. **`xlsx_price_loader.py`** - Price loading module
   - Reads XLSX price tables
   - Caches prices in memory
   - Auto-reloads on file modification

2. **`pricing_service.py`** - Pricing service
   - Integrates DMN rules (weight class, service determination)
   - Looks up prices from XLSX files
   - Calculates totals with tax

3. **DMN Integration** - Business rules
   - Weight classification → determines weight class
   - Service determination → determines applicable services
   - Prices looked up from XLSX for each service

### Data Flow

```
Order Data
    ↓
DMN Rules (XLSX)
    ↓
Weight Class (20A, 20B, 40A-40D)
    ↓
Price Lookup (XLSX) → Main Service Price
    ↓
Service Codes (123, 456, etc.)
    ↓
Price Lookup (XLSX) → Additional Service Prices
    ↓
Calculate Total
    ↓
Final Invoice
```

---

## Advantages of XLSX Storage

✅ **Easy Editing**: Business users can edit prices in Excel
✅ **No Code Deployment**: Changes don't require code release
✅ **Version Control**: XLSX files are tracked in Git
✅ **Automatic Reload**: Changes detected without service restart
✅ **Similar to DMN Rules**: Consistent approach for dynamic data
✅ **Audit Trail**: Git history shows who changed what

---

## Database vs. XLSX

| Feature | Database | XLSX Files |
|---------|----------|------------|
| Editing | SQL or admin UI | Excel |
| Deployment | Separate database migration | Git commit |
| Reload | Immediate | Auto-detect on file change |
| Backup | Database backup | Git history |
| Collaboration | Locks/transactions | Git merge |
| Business User | Needs admin UI | Uses Excel |

**Decision**: XLSX files chosen for consistency with DMN rules approach and ease of business user editing.

---

## Future Enhancements (Optional)

1. **Admin UI** - Web interface for price editing
2. **Price History** - Track price changes over time
3. **Currency Support** - Multi-currency pricing
4. **Approval Workflow** - Price changes require approval
5. **Price Validation** - Check for missing/invalid prices before loading
6. **Date Range Support** - Automatic price selection based on valid date ranges

---

## Testing

```bash
# Test price loader
cd billing-re/services/rating
python3 -c "
from xlsx_price_loader import XLSXPriceLoader
from pathlib import Path

loader = XLSXPriceLoader(Path('../../shared/price-tables'))
price = loader.get_main_service_price('123456', '20B', 'Export')
print(f'Main price for 20B Export: €{price}')
"

# Test pricing service
python3 -c "
from pricing_service import PricingService

service = PricingService()
result = service.calculate_order_price({
    'offer_code': '123456',
    'container_length': '20',
    'gross_weight': 23000,
    'direction': 'Export',
    'transport_type': 'KV',
    'dangerous_goods': False
})
print(f'Total: €{result[\"total\"]:.2f}')
"
```

---

**Last Updated**: 2025-09-29
**Status**: ✅ Production Ready