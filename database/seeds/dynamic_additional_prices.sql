-- Additional Service Prices
-- Generated from: Requirement documents/5_Preistabelle_Nebenleistungen.xlsx
-- Generated at: 2025-09-29T21:59:34.901503

-- Clear existing data (optional)
-- TRUNCATE TABLE additional_service_prices CASCADE;

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 18, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 36, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 18, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 36, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 15, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 30, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 15, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO additional_service_prices (service_code, description, price_type, price, currency, valid_from, valid_to)
VALUES ('456', '', 'FIXED', 30, 'EUR', '20250131', '20251231')
ON CONFLICT (service_code, valid_from)
DO UPDATE SET price = EXCLUDED.price, description = EXCLUDED.description, valid_to = EXCLUDED.valid_to, updated_at = NOW();
