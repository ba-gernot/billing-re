#!/usr/bin/env python3
"""
Generate SQL INSERT statements from pricing XLSX files
Enables dynamic pricing: update XLSX → regenerate SQL → reload DB
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

def generate_main_service_prices_sql(xlsx_file: str, output_file: str):
    """
    Generate SQL for main_service_prices table from 5_Preistabelle_Hauptleistungen_Einzelpreise.xlsx
    """
    print(f"📊 Reading main service prices from: {xlsx_file}")
    df = pd.read_excel(xlsx_file)

    print(f"   Found {len(df)} rows")
    print(f"   Columns: {df.columns.tolist()}")

    sql_statements = []
    sql_statements.append("-- Main Service Prices")
    sql_statements.append("-- Generated from: " + xlsx_file)
    sql_statements.append("-- Generated at: " + datetime.now().isoformat())
    sql_statements.append("")
    sql_statements.append("-- Clear existing data (optional)")
    sql_statements.append("-- TRUNCATE TABLE main_service_prices CASCADE;")
    sql_statements.append("")

    # Generate INSERT statements
    for idx, row in df.iterrows():
        # Map XLSX columns to database columns
        # Adjust column names based on actual XLSX structure
        try:
            # Example mapping - adjust to actual XLSX columns
            offer_code = row.get('Angebot', row.get('Offer', 'DEFAULT'))
            weight_class = row.get('Gewichtsklasse', row.get('WeightClass', '20A'))
            route = row.get('Route', row.get('Strecke', 'DEFAULT'))
            price = row.get('Preis', row.get('Price', 100.0))
            currency = row.get('Währung', row.get('Currency', 'EUR'))
            valid_from = row.get('gültig von', row.get('ValidFrom', '2024-01-01'))
            valid_to = row.get('gültig bis', row.get('ValidTo', '2099-12-31'))

            # Handle NaN values
            if pd.isna(offer_code):
                offer_code = 'DEFAULT'
            if pd.isna(price):
                continue  # Skip rows without price

            sql = f"""INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('{offer_code}', '{weight_class}', '{route}', {price}, '{currency}', '{valid_from}', '{valid_to}')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, valid_to = EXCLUDED.valid_to, updated_at = NOW();"""

            sql_statements.append(sql)
            sql_statements.append("")

        except Exception as e:
            print(f"   ⚠️  Warning: Skipping row {idx}: {e}")
            continue

    # Write to file
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))

    print(f"✅ Generated {len(sql_statements) // 3} INSERT statements")
    print(f"   Saved to: {output_file}")
    return output_file


def generate_additional_service_prices_sql(xlsx_file: str, output_file: str):
    """
    Generate SQL for additional_service_prices table from 5_Preistabelle_Nebenleistungen.xlsx
    """
    print(f"\n📊 Reading additional service prices from: {xlsx_file}")
    df = pd.read_excel(xlsx_file)

    print(f"   Found {len(df)} rows")
    print(f"   Columns: {df.columns.tolist()}")

    sql_statements = []
    sql_statements.append("-- Additional Service Prices")
    sql_statements.append("-- Generated from: " + xlsx_file)
    sql_statements.append("-- Generated at: " + datetime.now().isoformat())
    sql_statements.append("")
    sql_statements.append("-- Clear existing data (optional)")
    sql_statements.append("-- TRUNCATE TABLE additional_service_prices CASCADE;")
    sql_statements.append("")

    # Generate INSERT statements
    for idx, row in df.iterrows():
        try:
            # Map XLSX columns to database columns
            service_code = row.get('Leistungscode', row.get('ServiceCode', '456'))
            description = row.get('Beschreibung', row.get('Description', ''))
            price_type = row.get('Preistyp', row.get('PriceType', 'FIXED'))
            price = row.get('Preis', row.get('Price', 0.0))
            currency = row.get('Währung', row.get('Currency', 'EUR'))
            valid_from = row.get('gültig von', row.get('ValidFrom', '2024-01-01'))
            valid_to = row.get('gültig bis', row.get('ValidTo', '2099-12-31'))

            # Handle NaN values
            if pd.isna(service_code):
                continue
            if pd.isna(price):
                price = 0.0
            if pd.isna(description):
                description = ''

            # Escape single quotes in description
            description = str(description).replace("'", "''")

            sql = f"""INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('{service_code}', '{description}', '{price_type}', {price}, '{currency}', '{valid_from}', '{valid_to}')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();"""

            sql_statements.append(sql)
            sql_statements.append("")

        except Exception as e:
            print(f"   ⚠️  Warning: Skipping row {idx}: {e}")
            continue

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))

    print(f"✅ Generated {len(sql_statements) // 3} INSERT statements")
    print(f"   Saved to: {output_file}")
    return output_file


def generate_hardcoded_pricing_sql(output_file: str):
    """
    Generate hardcoded pricing SQL for the €383 test scenario
    Use when XLSX files are not available or as a baseline
    """
    print(f"\n📝 Generating hardcoded pricing SQL for €383 scenario...")

    sql = """-- Hardcoded Pricing for €383 Test Scenario
-- Generated at: """ + datetime.now().isoformat() + """

-- Main Service: 20B Export KV → €100
INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('123456', '20B', 'DE-US', 100.0, 'EUR', '2024-01-01', '2099-12-31')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, updated_at = NOW();

-- Trucking Service: 123 Zustellung → €18
INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('222', 'Trucking Service (Zustellung)', 'FIXED', 18.0, 'EUR', '2024-01-01', '2099-12-31')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, updated_at = NOW();

-- Security Surcharge KV: 456 → €15
INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', 'Security Surcharge KV (Dangerous Goods)', 'FIXED', 15.0, 'EUR', '2025-05-01', '2025-08-31')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, updated_at = NOW();

-- Waiting Time: 789 → €50 per unit
INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('789', 'Waiting Time (Per Unit)', 'PER_UNIT', 50.0, 'EUR', '2024-01-01', '2099-12-31')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, updated_at = NOW();

-- Generic Main Service: 111 → €100
INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('111', 'Generic Main Service', 'FIXED', 100.0, 'EUR', '2024-01-01', '2099-12-31')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, updated_at = NOW();

-- KV Service: 444 → €0 (included in main price)
INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('444', 'KV Service', 'FIXED', 0.0, 'EUR', '2024-01-01', '2099-12-31')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, updated_at = NOW();

"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(sql)

    print(f"✅ Generated hardcoded pricing SQL")
    print(f"   Saved to: {output_file}")
    return output_file


if __name__ == "__main__":
    print("🚀 Generating Pricing SQL from XLSX files...\n")

    # Paths
    req_docs = Path("Requirement documents")
    output_dir = Path("billing-re/database/seeds")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Try to generate from XLSX files
    main_prices_xlsx = req_docs / "5_Preistabelle_Hauptleistungen_Einzelpreise.xlsx"
    additional_prices_xlsx = req_docs / "5_Preistabelle_Nebenleistungen.xlsx"

    files_generated = []

    if main_prices_xlsx.exists():
        try:
            output = generate_main_service_prices_sql(
                str(main_prices_xlsx),
                str(output_dir / "dynamic_main_prices.sql")
            )
            files_generated.append(output)
        except Exception as e:
            print(f"❌ Failed to generate main prices SQL: {e}")
    else:
        print(f"⚠️  Main prices XLSX not found: {main_prices_xlsx}")

    if additional_prices_xlsx.exists():
        try:
            output = generate_additional_service_prices_sql(
                str(additional_prices_xlsx),
                str(output_dir / "dynamic_additional_prices.sql")
            )
            files_generated.append(output)
        except Exception as e:
            print(f"❌ Failed to generate additional prices SQL: {e}")
    else:
        print(f"⚠️  Additional prices XLSX not found: {additional_prices_xlsx}")

    # Always generate hardcoded baseline
    hardcoded_output = generate_hardcoded_pricing_sql(
        str(output_dir / "hardcoded_prices_383.sql")
    )
    files_generated.append(hardcoded_output)

    print(f"\n✅ All pricing SQL files generated!")
    print(f"\nGenerated files:")
    for f in files_generated:
        print(f"   • {f}")

    print(f"\n📝 To load into database:")
    print(f"   psql -d your_database -f billing-re/database/seeds/hardcoded_prices_383.sql")
    print(f"\n   Or add to database/connection.py for automatic sync on startup")