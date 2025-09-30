-- SQLite Mock Database Setup
-- Adapted from PostgreSQL schema for local testing

-- Core Pipeline Tables

-- 1. Operational Orders (Input stage)
CREATE TABLE operational_orders (
    id TEXT PRIMARY KEY,
    order_reference TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL,
    freightpayer_id TEXT NOT NULL,
    departure_date TEXT NOT NULL,
    arrival_date TEXT,
    transport_direction TEXT NOT NULL CHECK (transport_direction IN ('Export', 'Import', 'Domestic')),
    container_data TEXT NOT NULL,
    route_data TEXT,
    trucking_data TEXT,
    dangerous_goods_flag INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    raw_input TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 2. Service Orders (Transformation output)
CREATE TABLE service_orders (
    id TEXT PRIMARY KEY,
    operational_order_id TEXT NOT NULL,
    service_type TEXT NOT NULL CHECK (service_type IN ('MAIN', 'TRUCKING', 'ADDITIONAL')),
    service_code TEXT,
    description TEXT,
    quantity REAL DEFAULT 1,
    weight_class TEXT,
    route_from TEXT,
    route_to TEXT,
    loading_status TEXT,
    transport_type TEXT,
    service_data TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operational_order_id) REFERENCES operational_orders(id)
);

-- 3. Billing Documents (Rating + Pricing output)
CREATE TABLE billing_documents (
    id TEXT PRIMARY KEY,
    service_order_id TEXT NOT NULL,
    offer_id TEXT,
    base_price REAL NOT NULL,
    calculated_amount REAL NOT NULL,
    currency TEXT DEFAULT 'EUR',
    tax_case TEXT,
    tax_rate REAL,
    tax_amount REAL,
    total_amount REAL NOT NULL,
    pricing_details TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_order_id) REFERENCES service_orders(id)
);

-- 4. Invoice Documents (Final aggregated invoices)
CREATE TABLE invoice_documents (
    id TEXT PRIMARY KEY,
    invoice_number TEXT NOT NULL UNIQUE,
    operational_order_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    subtotal REAL NOT NULL,
    total_tax REAL NOT NULL,
    total_amount REAL NOT NULL,
    currency TEXT DEFAULT 'EUR',
    invoice_date TEXT DEFAULT CURRENT_TIMESTAMP,
    due_date TEXT,
    pdf_path TEXT,
    xml_path TEXT,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'cancelled')),
    metadata TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operational_order_id) REFERENCES operational_orders(id)
);

-- Master Data Tables

-- 5. Customers
CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    customer_group TEXT DEFAULT 'STANDARD' CHECK (customer_group IN ('PREMIUM', 'STANDARD')),
    vat_id TEXT,
    country_code TEXT,
    address TEXT,
    contact_info TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 6. Container Types
CREATE TABLE container_types (
    id TEXT PRIMARY KEY,
    iso_code TEXT NOT NULL UNIQUE,
    length_ft INTEGER NOT NULL,
    width_ft INTEGER DEFAULT 8,
    height_ft INTEGER DEFAULT 8,
    tare_weight_kg INTEGER NOT NULL,
    max_payload_kg INTEGER NOT NULL,
    max_gross_weight_kg INTEGER NOT NULL,
    description TEXT,
    is_active INTEGER DEFAULT 1
);

-- 7. Countries
CREATE TABLE countries (
    id TEXT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    eu_member INTEGER DEFAULT 0,
    default_vat_rate REAL,
    currency TEXT DEFAULT 'EUR',
    is_active INTEGER DEFAULT 1
);

-- Indexes for Performance
CREATE INDEX idx_operational_orders_customer ON operational_orders(customer_id, departure_date, status);
CREATE INDEX idx_operational_orders_reference ON operational_orders(order_reference);
CREATE INDEX idx_operational_orders_status ON operational_orders(status, created_at);
CREATE INDEX idx_billing_docs_service ON billing_documents(service_order_id);
CREATE INDEX idx_billing_docs_offer ON billing_documents(offer_id);
CREATE INDEX idx_invoice_docs_customer ON invoice_documents(customer_id, invoice_date);
CREATE INDEX idx_invoice_docs_order ON invoice_documents(operational_order_id);
CREATE INDEX idx_service_orders_operational ON service_orders(operational_order_id);
CREATE INDEX idx_billing_service_order ON billing_documents(service_order_id);

-- NOTE: Business rules and pricing are loaded dynamically from XLSX files:
-- - shared/price-tables/main_service_prices.xlsx
-- - shared/price-tables/additional_service_prices.xlsx
-- - shared/dmn-rules/service_determination.dmn.xlsx
-- - shared/dmn-rules/weight_class.dmn.xlsx
-- - shared/dmn-rules/tax_calculation.dmn.xlsx
-- - shared/dmn-rules/trip_type.dmn.xlsx