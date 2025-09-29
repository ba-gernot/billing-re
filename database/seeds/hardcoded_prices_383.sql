-- Hardcoded Pricing for €383 Test Scenario
-- Generated at: 2025-09-29T21:59:34.902242

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

