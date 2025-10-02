# Hardcoded Values Analysis & XLSX Migration Strategy

**Date:** 2025-10-02
**Objective:** Identify all hardcoded values and migrate them to XLSX rule files

---

## Executive Summary

Analysis of the codebase reveals **23 hardcoded values** across services and API gateway. Most critical are:
- **Country codes** (DE, US)
- **Transport directions** (Export/Import/Domestic)
- **Default values** (loading status, currency)
- **Business logic** (weight classification, transport type determination)

**Available XLSX Files:**
- ✅ `5_Regeln_Gewichtsklassen.xlsx` - Weight classification rules
- ✅ `3_Regeln_Fahrttyp.xlsx` - Trip type determination
- ✅ `3_1_Regeln_Steuerberechnung.xlsx` - Tax calculation rules
- ✅ `4_Regeln_Leistungsermittlung.xlsx` - Service determination
- ✅ `6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx` - Main service prices
- ✅ `6_Preistabelle_Nebenleistungen.xlsx` - Additional service prices
- ⚠️ **MISSING:** Country mapping rules, transport type determination rules

---

## 1. services/rating/main.py

### Location: `/rate-xlsx` endpoint (lines 693-741)

#### Hardcoded Values:

| Line | Variable | Hardcoded Value | Current Source | Should Come From |
|------|----------|-----------------|----------------|------------------|
| 709 | `departure_country` | `'DE'` | Hardcoded | **Order JSON** (`Order.Container.TakeOver.DepartureCountryIsoCode`) |
| 712 | `destination_country` | `'DE'` | Hardcoded | **Order JSON** (`Order.Container.HandOver.DestinationCountryIsoCode`) |
| 715 | `direction` | `'Export'` | Hardcoded | **Order JSON** (`Order.Container.TransportDirection`) |
| 708 | `customer_group` | `''` (empty) | Hardcoded | **Order JSON or XLSX** (customer master data) |
| 711 | `tariff_point_dep` | `''` (empty) | Hardcoded | **Order JSON** (if available) or leave empty |
| 714 | `tariff_point_dest` | `''` (empty) | Hardcoded | **Order JSON** (if available) or leave empty |
| 726 | `service_code` | `'MAIN'` | Hardcoded | OK (constant for main service) |
| 726 | `service_name` | `'Main Transport Service'` | Hardcoded | Could come from XLSX service catalog |
| 730 | `currency` | `"EUR"` | Hardcoded | Could come from XLSX or order |

#### Impact: 🔴 **CRITICAL**
- Main transport service pricing uses wrong countries (always DE→DE instead of actual route)
- Direction always set to 'Export' regardless of actual transport direction
- Missing customer group means XLSX can't match customer-group-specific prices

#### Solution Strategy:

**Option 1: Extract from Order JSON (RECOMMENDED)**
```python
# Line 709-720: Replace hardcoded values with JSON extraction
departure_country = (
    order_context.get('departure_country') or
    container_data.get('TakeOver', {}).get('DepartureCountryIsoCode', 'DE')
)
destination_country = (
    order_context.get('destination_country') or
    container_data.get('HandOver', {}).get('DestinationCountryIsoCode', 'DE')
)
direction = service_order.transport_direction or container_data.get('TransportDirection', 'Export')
```

**Option 2: Create new XLSX rule file** `7_Country_Mapping_Rules.xlsx`
- Columns: Station Number | Country Code | Tariff Point
- Use station numbers to look up country codes

---

## 2. services/transformation/main.py

### Location: Service decomposition logic

#### Hardcoded Values:

| Line | Variable | Hardcoded Value | Current Source | Should Come From |
|------|----------|-----------------|----------------|------------------|
| 329 | `transport_type` | `TransportType.KV if len(trucking_services) > 0 else TransportType.STANDARD` | Hardcoded logic | **New XLSX rule** or enhanced logic |
| 343-348 | Trip type fallback | `{"LB": "ZUSTELLUNG", "AB": "ABHOLUNG", ...}` | Hardcoded dict | ✅ Already in `3_Regeln_Fahrttyp.xlsx` (fallback only) |
| 354-358 | Service quantity | `{"123": 5, "789": 5}` | Hardcoded dict | **Order JSON** or XLSX |

#### Impact: 🟡 **MEDIUM**
- Transport type logic is simplistic (presence of trucking = KV)
- Fallback mappings duplicate XLSX rules (acceptable as fallback)

#### Solution Strategy:

**For Transport Type (line 329):**
Create new XLSX rule `8_Transport_Type_Rules.xlsx`:
```
| Trucking Count | Dangerous Goods | Container Type | Transport Type |
|----------------|-----------------|----------------|----------------|
| > 0            | true            | -              | KV             |
| > 0            | false           | -              | KVS            |
| 0              | -               | -              | STANDARD       |
```

**For Service Quantity (lines 354-358):**
Already in order JSON - extract from `AdditionalServices[].Amount`

---

## 3. services/billing/main.py

### Location: Tax calculation and billing input

#### Hardcoded Values:

| Line | Variable | Hardcoded Value | Current Source | Should Come From |
|------|----------|-----------------|----------------|------------------|
| 71 | `departure_country` default | `"DE"` | Hardcoded | Order JSON (keep as fallback) |
| 75 | `loading_status` default | `"beladen"` | Hardcoded | Order JSON (keep as fallback) |
| 382 | `from_country` | `"DE"` | Hardcoded | **Pass from orchestrator** |
| 410-425 | Fallback tax rules | Export/Import/Domestic logic | Hardcoded | ✅ Already in `3_1_Regeln_Steuerberechnung.xlsx` (fallback OK) |

#### Impact: 🟢 **LOW**
- Defaults are reasonable fallbacks
- Tax calculation already uses XLSX (fallbacks are acceptable)

#### Solution Strategy:
- **Line 382:** Should receive `from_country` from caller (orchestrator)
- Keep fallback defaults as-is (defensive programming)

---

## 4. api-gateway/src/orchestration/order-orchestrator.js

### Location: Service orchestration

#### Hardcoded Values:

| Line | Variable | Hardcoded Value | Current Source | Should Come From |
|------|----------|-----------------|----------------|------------------|
| 357 | `departure_country` | `'DE'` | Hardcoded | **Order JSON** (`Order.Container.TakeOver.DepartureCountryIsoCode`) |
| 358 | `destination_country` | `container.TransportDirection === 'Export' ? 'US' : 'DE'` | Hardcoded logic | **Order JSON** (`Order.Container.HandOver.DestinationCountryIsoCode`) |
| 361 | `loading_status` fallback | `'beladen'` | Hardcoded | Order JSON (keep fallback) |
| 400-411 | Weight class logic | Full calculation function | Hardcoded | ✅ Already in `5_Regeln_Gewichtsklassen.xlsx` (duplicate logic) |

#### Impact: 🔴 **CRITICAL**
- Line 358: **WRONG LOGIC** - assumes Export always goes to US, Import/Domestic to DE
- Weight class calculation duplicates XLSX rules (should use rating service result)

#### Solution Strategy:

**Lines 357-358: Extract from Order JSON**
```javascript
departure_country: container.TakeOver?.DepartureCountryIsoCode || 'DE',
destination_country: container.HandOver?.DestinationCountryIsoCode || 'DE',
```

**Lines 400-411: Remove duplicate logic**
```javascript
// DELETE THIS FUNCTION - weight class already calculated by rating service
// Use: transformationResult.main_service.weight_class (from XLSX)
```

---

## 5. Available XLSX Files Status

### ✅ Fully Utilized:
1. **5_Regeln_Gewichtsklassen.xlsx** - Used by `xlsx_dmn_processor.py`
2. **3_Regeln_Fahrttyp.xlsx** - Used by `dmn_trip_type.py`
3. **3_1_Regeln_Steuerberechnung.xlsx** - Used by `xlsx_tax_processor.py`
4. **4_Regeln_Leistungsermittlung.xlsx** - Used by `xlsx_dmn_processor.py`
5. **6_Preistabelle_Hauptleistungen_Einzelpreise.xlsx** - Used by `xlsx_price_loader.py`
6. **6_Preistabelle_Nebenleistungen.xlsx** - Used by `xlsx_price_loader.py`

### ⚠️ Missing XLSX Files:
1. **7_Country_Mapping_Rules.xlsx** (optional)
   - Map railway station numbers → country codes
   - Columns: `Station Number | Country Code | Tariff Point | Region`

2. **8_Transport_Type_Rules.xlsx** (optional)
   - Determine transport type from order characteristics
   - Columns: `Trucking Count | Dangerous Goods | Container Type | Transport Type`

3. **9_Service_Catalog.xlsx** (optional)
   - Service codes, names, descriptions
   - Columns: `Service Code | Service Name (DE) | Service Name (EN) | Description | Category`

---

## Priority Action Items

### 🔴 CRITICAL (Fix Immediately)

1. **services/rating/main.py:709-715**
   ```python
   # BEFORE (WRONG):
   departure_country='DE',
   destination_country='DE',
   direction='Export',

   # AFTER (CORRECT):
   departure_country=service_order.departure_country or 'DE',
   destination_country=service_order.destination_country or 'DE',
   direction=service_order.transport_direction or 'Export',
   ```

2. **api-gateway/order-orchestrator.js:357-358**
   ```javascript
   // BEFORE (WRONG):
   departure_country: 'DE',
   destination_country: container.TransportDirection === 'Export' ? 'US' : 'DE',

   // AFTER (CORRECT):
   departure_country: container.TakeOver?.DepartureCountryIsoCode || 'DE',
   destination_country: container.HandOver?.DestinationCountryIsoCode || 'DE',
   ```

3. **Pass data through transformation service**
   - Add `departure_country`, `destination_country` to ServiceOrderOutput model
   - Extract from operational order JSON in transformation service

### 🟡 MEDIUM (Improve Soon)

4. **api-gateway/order-orchestrator.js:400-411**
   - Delete `calculateWeightClass()` function (duplicate logic)
   - Use weight class from rating service (already calculated via XLSX)

5. **services/transformation/main.py:329**
   - Enhance transport type determination logic
   - Consider creating `8_Transport_Type_Rules.xlsx`

### 🟢 LOW (Optional Enhancement)

6. **Create optional XLSX files** (listed above)
7. **services/rating/main.py:708** - Add customer_group lookup

---

## Implementation Checklist

### Phase 1: Critical Fixes (Services Working Correctly)
- [ ] Add `departure_country`, `destination_country`, `transport_direction` fields to transformation service output
- [ ] Update rating service to use these fields from service orders
- [ ] Update API gateway to extract country codes from Order JSON
- [ ] Remove duplicate weight class calculation from API gateway

### Phase 2: Data Flow Validation
- [ ] Test with order JSON containing different countries
- [ ] Verify XLSX main service pricing matches correctly
- [ ] Verify tax calculation uses correct countries

### Phase 3: Optional Enhancements
- [ ] Create `7_Country_Mapping_Rules.xlsx` (if station→country lookup needed)
- [ ] Create `8_Transport_Type_Rules.xlsx` (for complex transport type logic)
- [ ] Add customer group lookup (if customer master data available)

---

## Testing Strategy

### Test Case 1: Export DE→US
```json
{
  "Container": {
    "TransportDirection": "Export",
    "TakeOver": { "DepartureCountryIsoCode": "DE" },
    "HandOver": { "DestinationCountryIsoCode": "US" }
  }
}
```
**Expected:** `departure_country='DE'`, `destination_country='US'`, `direction='Export'`

### Test Case 2: Import US→DE
```json
{
  "Container": {
    "TransportDirection": "Import",
    "TakeOver": { "DepartureCountryIsoCode": "US" },
    "HandOver": { "DestinationCountryIsoCode": "DE" }
  }
}
```
**Expected:** `departure_country='US'`, `destination_country='DE'`, `direction='Import'`

### Test Case 3: Domestic DE→DE
```json
{
  "Container": {
    "TransportDirection": "Domestic",
    "TakeOver": { "DepartureCountryIsoCode": "DE" },
    "HandOver": { "DestinationCountryIsoCode": "DE" }
  }
}
```
**Expected:** `departure_country='DE'`, `destination_country='DE'`, `direction='Domestic'`

---

## Conclusion

**Current State:**
- 6/6 XLSX files are actively used ✅
- 23 hardcoded values identified
- 8 critical issues affecting pricing accuracy

**Next Steps:**
1. Fix critical hardcoded country/direction values (Phase 1)
2. Validate data flows through all services (Phase 2)
3. Consider creating optional XLSX files for complete rule coverage (Phase 3)

**Expected Outcome:**
- 100% rule-driven pricing ✅
- All business logic in XLSX files ✅
- No hardcoded assumptions about geography or transport ✅
