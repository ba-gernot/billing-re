-- Billing RE System - Master Data Seeds
-- Version: 002
-- Description: Essential master data for development and testing

BEGIN;

-- Container Types (from roadmap examples)
INSERT INTO container_types (iso_code, length_ft, tare_weight_kg, max_payload_kg, max_gross_weight_kg, description) VALUES
('22G1', 20, 2000, 21000, 23000, '20ft General Purpose Container'),
('42G1', 40, 3000, 27000, 30000, '40ft General Purpose Container'),
('22R1', 20, 2200, 20800, 23000, '20ft Reefer Container'),
('42R1', 40, 3500, 26500, 30000, '40ft Reefer Container'),
('22T1', 20, 2100, 20900, 23000, '20ft Tank Container'),
('22P1', 20, 1800, 21200, 23000, '20ft Platform Container');

-- Countries (EU focus)
INSERT INTO countries (code, name, eu_member, default_vat_rate, currency) VALUES
('DE', 'Germany', TRUE, 0.19, 'EUR'),
('FR', 'France', TRUE, 0.20, 'EUR'),
('NL', 'Netherlands', TRUE, 0.21, 'EUR'),
('BE', 'Belgium', TRUE, 0.21, 'EUR'),
('IT', 'Italy', TRUE, 0.22, 'EUR'),
('ES', 'Spain', TRUE, 0.21, 'EUR'),
('PL', 'Poland', TRUE, 0.23, 'EUR'),
('US', 'United States', FALSE, 0.00, 'USD'),
('CN', 'China', FALSE, 0.00, 'CNY'),
('GB', 'United Kingdom', FALSE, 0.20, 'GBP');

-- Customers (from roadmap examples)
INSERT INTO customers (code, name, customer_group, vat_id, country_code) VALUES
('123456', 'Premium Logistics GmbH', 'PREMIUM', 'DE123456789', 'DE'),
('234567', 'Standard Transport AG', 'STANDARD', 'DE234567890', 'DE'),
('345678', 'Express Shipping Ltd', 'PREMIUM', 'GB345678901', 'GB'),
('456789', 'Global Freight Inc', 'STANDARD', 'US456789012', 'US'),
('567890', 'Europa Container BV', 'PREMIUM', 'NL567890123', 'NL');

-- Weight Class Rules (from roadmap section 4)
INSERT INTO weight_class_rules (container_length, min_weight_kg, max_weight_kg, weight_class, description) VALUES
(20, 0, 20000, '20A', '20ft container up to 20 tons'),
(20, 20001, NULL, '20B', '20ft container over 20 tons'),
(40, 0, 25000, '40A', '40ft container up to 25 tons'),
(40, 25001, NULL, '40B', '40ft container over 25 tons');

-- Service Rules (key business rules from roadmap)
INSERT INTO service_rules (rule_name, rule_type, conditions, service_code, description, priority, valid_from, valid_to) VALUES
('KV Dangerous Security', 'SERVICE_DETERMINATION',
 '{"transport_type": "KV", "dangerous_goods": true, "date_range": {"from": "2025-05-01", "to": "2025-08-31"}}',
 '456', 'Security surcharge for KV dangerous goods (seasonal)', 1, '2025-05-01', '2025-08-31'),

('KV Main Dangerous Security', 'SERVICE_DETERMINATION',
 '{"service_type": "MAIN", "loading_status": ["beladen", "leer"], "transport_type": "KV", "dangerous_goods": true}',
 '456', 'Security surcharge for main KV dangerous', 2, '2024-01-01', NULL),

('KV Standard Service', 'SERVICE_DETERMINATION',
 '{"service_type": "MAIN", "loading_status": ["beladen", "leer"], "transport_type": "KV"}',
 '444', 'Standard KV service', 3, '2024-01-01', NULL),

('Generic Main Service', 'SERVICE_DETERMINATION',
 '{"service_type": "MAIN"}',
 '111', 'Generic main service fallback', 10, '2024-01-01', NULL),

('Generic Trucking Service', 'SERVICE_DETERMINATION',
 '{"service_type": "TRUCKING"}',
 '222', 'Generic trucking service', 10, '2024-01-01', NULL),

('Station Security Hamburg', 'SERVICE_DETERMINATION',
 '{"station_codes": ["80155283", "80137943"]}',
 '333', 'Security service for specific Hamburg stations', 5, '2024-01-01', NULL),

('Customs Documentation', 'SERVICE_DETERMINATION',
 '{"customs_type": "N1", "country": "DE"}',
 '555', 'Customs documentation service', 5, '2024-01-01', NULL),

('Waiting Time Service', 'SERVICE_DETERMINATION',
 '{"additional_services": {"exists": true}}',
 '789', 'Waiting time charged per quantity', 6, '2024-01-01', NULL);

-- Tax Rules (from roadmap section 6)
INSERT INTO tax_rules (rule_name, conditions, tax_case, tax_rate, description, valid_from) VALUES
('Export VAT Exemption',
 '{"transport_direction": "Export", "from_country": "DE"}',
 '§4 No. 3a UStG', 0.00, 'Export transactions VAT exempt', '2024-01-01'),

('Import Reverse Charge',
 '{"transport_direction": "Import", "to_country": "DE"}',
 'Reverse charge', 0.00, 'Import reverse charge mechanism', '2024-01-01'),

('Domestic Standard VAT',
 '{"transport_direction": "Domestic", "from_country": "DE", "to_country": "DE"}',
 'Standard VAT', 0.19, 'Domestic German VAT 19%', '2024-01-01'),

('EU Standard VAT',
 '{"transport_direction": "Export", "from_country": "DE", "to_eu": true}',
 'EU VAT', 0.19, 'Intra-EU transport VAT', '2024-01-01');

-- Main Service Prices (from roadmap pricing example)
INSERT INTO main_service_prices (customer_id, offer_code, weight_class, transport_direction, price, minimum_price, unit, valid_from) VALUES
-- Premium customer prices
((SELECT id FROM customers WHERE code = '123456'), 'OFFER_123456', '20B', 'Export', 100.00, 100.00, 'per_container', '2024-01-01'),
((SELECT id FROM customers WHERE code = '123456'), 'OFFER_123456', '20A', 'Export', 80.00, 80.00, 'per_container', '2024-01-01'),
((SELECT id FROM customers WHERE code = '123456'), 'OFFER_123456', '40A', 'Export', 120.00, 120.00, 'per_container', '2024-01-01'),
((SELECT id FROM customers WHERE code = '123456'), 'OFFER_123456', '40B', 'Export', 150.00, 150.00, 'per_container', '2024-01-01'),

-- Standard customer prices
((SELECT id FROM customers WHERE code = '234567'), 'STANDARD_RATES', '20B', 'Export', 110.00, 110.00, 'per_container', '2024-01-01'),
((SELECT id FROM customers WHERE code = '234567'), 'STANDARD_RATES', '20A', 'Export', 90.00, 90.00, 'per_container', '2024-01-01'),
((SELECT id FROM customers WHERE code = '234567'), 'STANDARD_RATES', '40A', 'Export', 130.00, 130.00, 'per_container', '2024-01-01'),
((SELECT id FROM customers WHERE code = '234567'), 'STANDARD_RATES', '40B', 'Export', 160.00, 160.00, 'per_container', '2024-01-01');

-- Additional Service Prices (from roadmap examples)
INSERT INTO additional_service_prices (service_code, service_name, price_type, price, valid_from) VALUES
('222', 'Trucking Service - Zustellung', 'fixed', 18.00, '2024-01-01'),
('222', 'Trucking Service - Abholung', 'fixed', 20.00, '2024-01-01'),
('456', 'Security Service - KV Dangerous', 'fixed', 15.00, '2024-01-01'),
('333', 'Station Security', 'fixed', 25.00, '2024-01-01'),
('555', 'Customs Documentation', 'fixed', 35.00, '2024-01-01'),
('789', 'Waiting Time', 'per_unit', 50.00, '2024-01-01'),
('111', 'Generic Main Service', 'fixed', 75.00, '2024-01-01'),
('444', 'Standard KV Service', 'fixed', 85.00, '2024-01-01');

COMMIT;