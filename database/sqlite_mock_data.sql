-- SQLite Mock Data
-- Matches PostgreSQL seed data structure

-- Container Types
INSERT INTO container_types (id, iso_code, length_ft, tare_weight_kg, max_payload_kg, max_gross_weight_kg, description) VALUES
('ct-1', '22G1', 20, 2000, 21000, 23000, '20ft General Purpose Container'),
('ct-2', '42G1', 40, 3000, 27000, 30000, '40ft General Purpose Container'),
('ct-3', '22R1', 20, 2200, 20800, 23000, '20ft Reefer Container'),
('ct-4', '42R1', 40, 3500, 26500, 30000, '40ft Reefer Container'),
('ct-5', '22T1', 20, 2100, 20900, 23000, '20ft Tank Container'),
('ct-6', '22P1', 20, 1800, 21200, 23000, '20ft Platform Container');

-- Countries
INSERT INTO countries (id, code, name, eu_member, default_vat_rate, currency) VALUES
('co-1', 'DE', 'Germany', 1, 0.19, 'EUR'),
('co-2', 'FR', 'France', 1, 0.20, 'EUR'),
('co-3', 'NL', 'Netherlands', 1, 0.21, 'EUR'),
('co-4', 'BE', 'Belgium', 1, 0.21, 'EUR'),
('co-5', 'IT', 'Italy', 1, 0.22, 'EUR'),
('co-6', 'ES', 'Spain', 1, 0.21, 'EUR'),
('co-7', 'PL', 'Poland', 1, 0.23, 'EUR'),
('co-8', 'US', 'United States', 0, 0.00, 'USD'),
('co-9', 'CN', 'China', 0, 0.00, 'CNY'),
('co-10', 'GB', 'United Kingdom', 0, 0.20, 'GBP');

-- Customers
INSERT INTO customers (id, code, name, customer_group, vat_id, country_code) VALUES
('cust-1', '123456', 'Premium Logistics GmbH', 'PREMIUM', 'DE123456789', 'DE'),
('cust-2', '234567', 'Standard Transport AG', 'STANDARD', 'DE234567890', 'DE'),
('cust-3', '345678', 'Express Shipping Ltd', 'PREMIUM', 'GB345678901', 'GB'),
('cust-4', '456789', 'Global Freight Inc', 'STANDARD', 'US456789012', 'US'),
('cust-5', '567890', 'Europa Container BV', 'PREMIUM', 'NL567890123', 'NL');

-- NOTE: Business rules and pricing data are loaded from XLSX files at runtime
-- See shared/price-tables/ and shared/dmn-rules/ directories

-- Sample Operational Orders
INSERT INTO operational_orders (id, order_reference, customer_id, freightpayer_id, departure_date, arrival_date, transport_direction, container_data, route_data, trucking_data, dangerous_goods_flag, status, raw_input) VALUES
('op-1', 'ORD-2024-001', 'cust-1', 'cust-1', '2024-03-15 08:00:00', '2024-03-18 14:00:00', 'Export',
 '{"containers": [{"iso_code": "22G1", "container_number": "ABCU1234567", "gross_weight_kg": 22000, "tare_weight_kg": 2000, "loading_status": "beladen"}]}',
 '{"from": "Hamburg", "to": "Rotterdam", "from_country": "DE", "to_country": "NL"}',
 '{"pickup_location": "Hamburg Port Terminal", "delivery_location": "Rotterdam APM"}',
 0, 'completed',
 '{"order_id": "ORD-2024-001", "customer_code": "123456", "containers": [{"iso_code": "22G1", "gross_weight": 22000}]}'),

('op-2', 'ORD-2024-002', 'cust-1', 'cust-1', '2024-03-20 10:00:00', '2024-03-23 16:00:00', 'Export',
 '{"containers": [{"iso_code": "42G1", "container_number": "MSCU9876543", "gross_weight_kg": 28000, "tare_weight_kg": 3000, "loading_status": "beladen"}]}',
 '{"from": "Hamburg", "to": "Antwerp", "from_country": "DE", "to_country": "BE"}',
 '{"pickup_location": "Hamburg Warehouse A", "delivery_location": "Antwerp Container Terminal"}',
 1, 'completed',
 '{"order_id": "ORD-2024-002", "customer_code": "123456", "containers": [{"iso_code": "42G1", "gross_weight": 28000, "dangerous_goods": true}]}'),

('op-3', 'ORD-2024-003', 'cust-2', 'cust-2', '2024-03-25 09:00:00', '2024-03-28 15:00:00', 'Import',
 '{"containers": [{"iso_code": "22G1", "container_number": "TCNU1122334", "gross_weight_kg": 18000, "tare_weight_kg": 2000, "loading_status": "beladen"}]}',
 '{"from": "Rotterdam", "to": "Hamburg", "from_country": "NL", "to_country": "DE"}',
 '{"pickup_location": "Rotterdam Maasvlakte", "delivery_location": "Hamburg Distribution Center"}',
 0, 'completed',
 '{"order_id": "ORD-2024-003", "customer_code": "234567", "containers": [{"iso_code": "22G1", "gross_weight": 18000}]}'),

('op-4', 'ORD-2024-004', 'cust-2', 'cust-2', '2024-04-01 07:30:00', NULL, 'Export',
 '{"containers": [{"iso_code": "42G1", "container_number": "COSU5544332", "gross_weight_kg": 24000, "tare_weight_kg": 3000, "loading_status": "beladen"}]}',
 '{"from": "Hamburg", "to": "Le Havre", "from_country": "DE", "to_country": "FR"}',
 '{"pickup_location": "Hamburg Central Depot"}',
 0, 'processing',
 '{"order_id": "ORD-2024-004", "customer_code": "234567", "containers": [{"iso_code": "42G1", "gross_weight": 24000}]}');

-- Sample Service Orders
INSERT INTO service_orders (id, operational_order_id, service_type, service_code, description, quantity, weight_class, route_from, route_to, loading_status, transport_type, service_data) VALUES
('so-1', 'op-1', 'MAIN', '111', 'Main transport service', 1, '20B', 'Hamburg', 'Rotterdam', 'beladen', 'KV',
 '{"container_iso": "22G1", "weight": 22000}'),
('so-2', 'op-1', 'TRUCKING', '222', 'Pickup trucking service', 1, NULL, 'Hamburg', NULL, NULL, NULL,
 '{"service_subtype": "Abholung", "location": "Hamburg Port Terminal"}'),
('so-3', 'op-1', 'TRUCKING', '222', 'Delivery trucking service', 1, NULL, NULL, 'Rotterdam', NULL, NULL,
 '{"service_subtype": "Zustellung", "location": "Rotterdam APM"}'),

('so-4', 'op-2', 'MAIN', '111', 'Main transport service', 1, '40B', 'Hamburg', 'Antwerp', 'beladen', 'KV',
 '{"container_iso": "42G1", "weight": 28000}'),
('so-5', 'op-2', 'ADDITIONAL', '456', 'Security service for dangerous goods', 1, NULL, NULL, NULL, NULL, NULL,
 '{"reason": "dangerous_goods"}'),
('so-6', 'op-2', 'TRUCKING', '222', 'Pickup trucking service', 1, NULL, 'Hamburg', NULL, NULL, NULL,
 '{"service_subtype": "Abholung", "location": "Hamburg Warehouse A"}'),

('so-7', 'op-3', 'MAIN', '111', 'Main transport service', 1, '20A', 'Rotterdam', 'Hamburg', 'beladen', 'KV',
 '{"container_iso": "22G1", "weight": 18000}'),
('so-8', 'op-3', 'TRUCKING', '222', 'Delivery trucking service', 1, NULL, NULL, 'Hamburg', NULL, NULL,
 '{"service_subtype": "Zustellung", "location": "Hamburg Distribution Center"}');

-- Sample Billing Documents
INSERT INTO billing_documents (id, service_order_id, offer_id, base_price, calculated_amount, currency, tax_case, tax_rate, tax_amount, total_amount, pricing_details) VALUES
('bd-1', 'so-1', 'OFFER_123456', 100.00, 100.00, 'EUR', '§4 No. 3a UStG', 0.00, 0.00, 100.00,
 '{"weight_class": "20B", "container_type": "22G1", "pricing_rule": "Premium customer offer"}'),
('bd-2', 'so-2', NULL, 20.00, 20.00, 'EUR', '§4 No. 3a UStG', 0.00, 0.00, 20.00,
 '{"service_type": "Abholung", "pricing_rule": "Standard trucking rate"}'),
('bd-3', 'so-3', NULL, 18.00, 18.00, 'EUR', '§4 No. 3a UStG', 0.00, 0.00, 18.00,
 '{"service_type": "Zustellung", "pricing_rule": "Standard trucking rate"}'),

('bd-4', 'so-4', 'OFFER_123456', 150.00, 150.00, 'EUR', '§4 No. 3a UStG', 0.00, 0.00, 150.00,
 '{"weight_class": "40B", "container_type": "42G1", "pricing_rule": "Premium customer offer"}'),
('bd-5', 'so-5', NULL, 15.00, 15.00, 'EUR', '§4 No. 3a UStG', 0.00, 0.00, 15.00,
 '{"service_code": "456", "pricing_rule": "Dangerous goods security"}'),
('bd-6', 'so-6', NULL, 20.00, 20.00, 'EUR', '§4 No. 3a UStG', 0.00, 0.00, 20.00,
 '{"service_type": "Abholung", "pricing_rule": "Standard trucking rate"}'),

('bd-7', 'so-7', 'STANDARD_RATES', 90.00, 90.00, 'EUR', 'Reverse charge', 0.00, 0.00, 90.00,
 '{"weight_class": "20A", "container_type": "22G1", "pricing_rule": "Standard customer rates"}'),
('bd-8', 'so-8', NULL, 18.00, 18.00, 'EUR', 'Reverse charge', 0.00, 0.00, 18.00,
 '{"service_type": "Zustellung", "pricing_rule": "Standard trucking rate"}');

-- Sample Invoice Documents
INSERT INTO invoice_documents (id, invoice_number, operational_order_id, customer_id, subtotal, total_tax, total_amount, currency, invoice_date, due_date, status, metadata) VALUES
('inv-1', 'INV-2024-001', 'op-1', 'cust-1', 138.00, 0.00, 138.00, 'EUR', '2024-03-18 16:00:00', '2024-04-18 16:00:00', 'sent',
 '{"order_reference": "ORD-2024-001", "service_count": 3, "tax_reason": "Export VAT exemption"}'),

('inv-2', 'INV-2024-002', 'op-2', 'cust-1', 185.00, 0.00, 185.00, 'EUR', '2024-03-23 18:00:00', '2024-04-23 18:00:00', 'sent',
 '{"order_reference": "ORD-2024-002", "service_count": 3, "tax_reason": "Export VAT exemption", "notes": "Dangerous goods surcharge applied"}'),

('inv-3', 'INV-2024-003', 'op-3', 'cust-2', 108.00, 0.00, 108.00, 'EUR', '2024-03-28 17:00:00', '2024-04-28 17:00:00', 'sent',
 '{"order_reference": "ORD-2024-003", "service_count": 2, "tax_reason": "Import reverse charge"}');