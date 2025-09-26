-- Billing RE System - Initial Database Schema
-- Version: 001
-- Description: Core tables for operational orders, service orders, billing, and master data

BEGIN;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable JSON functions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Core Pipeline Tables

-- 1. Operational Orders (Input stage)
CREATE TABLE operational_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_reference VARCHAR(50) NOT NULL UNIQUE,
    customer_id UUID NOT NULL,
    freightpayer_id UUID NOT NULL,
    departure_date TIMESTAMP NOT NULL,
    arrival_date TIMESTAMP,
    transport_direction VARCHAR(20) NOT NULL CHECK (transport_direction IN ('Export', 'Import', 'Domestic')),
    container_data JSONB NOT NULL,
    route_data JSONB,
    trucking_data JSONB,
    dangerous_goods_flag BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    raw_input JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Service Orders (Transformation output)
CREATE TABLE service_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operational_order_id UUID NOT NULL REFERENCES operational_orders(id),
    service_type VARCHAR(20) NOT NULL CHECK (service_type IN ('MAIN', 'TRUCKING', 'ADDITIONAL')),
    service_code VARCHAR(10),
    description TEXT,
    quantity DECIMAL(10,3) DEFAULT 1,
    weight_class VARCHAR(10),
    route_from VARCHAR(20),
    route_to VARCHAR(20),
    loading_status VARCHAR(20),
    transport_type VARCHAR(20),
    service_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Billing Documents (Rating + Pricing output)
CREATE TABLE billing_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_order_id UUID NOT NULL REFERENCES service_orders(id),
    offer_id VARCHAR(50),
    base_price DECIMAL(10,2) NOT NULL,
    calculated_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    tax_case VARCHAR(50),
    tax_rate DECIMAL(5,4),
    tax_amount DECIMAL(10,2),
    total_amount DECIMAL(10,2) NOT NULL,
    pricing_details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Invoice Documents (Final aggregated invoices)
CREATE TABLE invoice_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number VARCHAR(50) NOT NULL UNIQUE,
    operational_order_id UUID NOT NULL REFERENCES operational_orders(id),
    customer_id UUID NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    total_tax DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    pdf_path VARCHAR(500),
    xml_path VARCHAR(500),
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'cancelled')),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Master Data Tables

-- 5. Customers
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(20) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    customer_group VARCHAR(20) DEFAULT 'STANDARD' CHECK (customer_group IN ('PREMIUM', 'STANDARD')),
    vat_id VARCHAR(50),
    country_code VARCHAR(2),
    address JSONB,
    contact_info JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Container Types
CREATE TABLE container_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    iso_code VARCHAR(10) NOT NULL UNIQUE,
    length_ft INTEGER NOT NULL,
    width_ft INTEGER DEFAULT 8,
    height_ft INTEGER DEFAULT 8,
    tare_weight_kg INTEGER NOT NULL,
    max_payload_kg INTEGER NOT NULL,
    max_gross_weight_kg INTEGER NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 7. Countries
CREATE TABLE countries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(2) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    eu_member BOOLEAN DEFAULT FALSE,
    default_vat_rate DECIMAL(5,4),
    currency VARCHAR(3) DEFAULT 'EUR',
    is_active BOOLEAN DEFAULT TRUE
);

-- Rules and Pricing Tables

-- 8. Service Rules (DMN business rules)
CREATE TABLE service_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,
    conditions JSONB NOT NULL,
    service_code VARCHAR(10) NOT NULL,
    description TEXT,
    priority INTEGER DEFAULT 100,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    dmn_file_path VARCHAR(500),
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 9. Weight Class Rules
CREATE TABLE weight_class_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    container_length INTEGER NOT NULL,
    min_weight_kg INTEGER NOT NULL,
    max_weight_kg INTEGER,
    weight_class VARCHAR(10) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. Tax Rules
CREATE TABLE tax_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_name VARCHAR(100) NOT NULL,
    conditions JSONB NOT NULL,
    tax_case VARCHAR(100) NOT NULL,
    tax_rate DECIMAL(5,4) NOT NULL,
    description TEXT,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Main Service Prices
CREATE TABLE main_service_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id),
    offer_code VARCHAR(50),
    weight_class VARCHAR(10),
    transport_direction VARCHAR(20),
    route_from VARCHAR(20),
    route_to VARCHAR(20),
    price DECIMAL(10,2) NOT NULL,
    minimum_price DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    unit VARCHAR(20) DEFAULT 'per_container',
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 12. Additional Service Prices
CREATE TABLE additional_service_prices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service_code VARCHAR(10) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    price_type VARCHAR(20) NOT NULL CHECK (price_type IN ('fixed', 'percentage', 'per_unit')),
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance

-- Operational Orders
CREATE INDEX idx_operational_orders_customer ON operational_orders(customer_id, departure_date, status);
CREATE INDEX idx_operational_orders_reference ON operational_orders(order_reference);
CREATE INDEX idx_operational_orders_status ON operational_orders(status, created_at);

-- Service Rules (Critical for rule application)
CREATE INDEX idx_service_rules_active ON service_rules(is_active, valid_from, valid_to) WHERE is_active = true;
CREATE INDEX idx_service_rules_type ON service_rules(rule_type, is_active);

-- Main Prices (Critical for pricing lookups)
CREATE INDEX idx_main_prices_lookup ON main_service_prices(customer_id, weight_class, transport_direction, valid_from, valid_to) WHERE is_active = true;
CREATE INDEX idx_main_prices_offer ON main_service_prices(offer_code, valid_from, valid_to) WHERE is_active = true;

-- Additional Prices
CREATE INDEX idx_additional_prices_code ON additional_service_prices(service_code, valid_from, valid_to) WHERE is_active = true;

-- Weight Classes
CREATE INDEX idx_weight_classes ON weight_class_rules(container_length, min_weight_kg, max_weight_kg) WHERE is_active = true;

-- Billing Documents
CREATE INDEX idx_billing_docs_service ON billing_documents(service_order_id);
CREATE INDEX idx_billing_docs_offer ON billing_documents(offer_id);

-- Invoice Documents
CREATE INDEX idx_invoice_docs_customer ON invoice_documents(customer_id, invoice_date);
CREATE INDEX idx_invoice_docs_order ON invoice_documents(operational_order_id);

-- Foreign Key Indexes
CREATE INDEX idx_service_orders_operational ON service_orders(operational_order_id);
CREATE INDEX idx_billing_service_order ON billing_documents(service_order_id);

-- Triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_operational_orders_updated_at BEFORE UPDATE ON operational_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_service_rules_updated_at BEFORE UPDATE ON service_rules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;