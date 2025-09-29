-- Main Service Prices
-- Generated from: Requirement documents/5_Preistabelle_Hauptleistungen_Einzelpreise.xlsx
-- Generated at: 2025-09-29T21:59:34.896123

-- Clear existing data (optional)
-- TRUNCATE TABLE main_service_prices CASCADE;

INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('DEFAULT', '20A', 'DEFAULT', 100, 'EUR', '20250131', '20251231')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('DEFAULT', '20A', 'DEFAULT', 150, 'EUR', '20250131', '20251231')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('DEFAULT', '20A', 'DEFAULT', 200, 'EUR', '20250131', '20251231')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('DEFAULT', '20A', 'DEFAULT', 210, 'EUR', '20250131', '20251231')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('DEFAULT', '20A', 'DEFAULT', 220, 'EUR', '20250131', '20251231')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, valid_to = EXCLUDED.valid_to, updated_at = NOW();

INSERT INTO main_service_prices (offer_code, weight_class, route, price, currency, valid_from, valid_to)
VALUES ('DEFAULT', '20A', 'DEFAULT', 230, 'EUR', '20250131', '20251231')
ON CONFLICT (offer_code, weight_class, route, valid_from)
DO UPDATE SET price = EXCLUDED.price, valid_to = EXCLUDED.valid_to, updated_at = NOW();
