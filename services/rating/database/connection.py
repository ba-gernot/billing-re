import os
import asyncpg
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)
import json
from datetime import datetime

class RatingDatabaseConnection:
    """Database connection manager for rating service with rule and pricing lookups"""

    def __init__(self):
        self.connection_pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv("DATABASE_URL", "postgresql://billing_user:billing_pass@localhost:5432/billing_re")

    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("Rating service database connection pool initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize database connection: {e}")
            logger.warning("Running without database - XLSX processors will still work")
            self.connection_pool = None  # Allow service to start without database

    async def close(self):
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Rating service database connection pool closed")

    async def get_active_service_rules(self, rule_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all active service rules, optionally filtered by type"""
        if self.connection_pool is None:
            logger.warning("Database not available - returning empty service rules")
            return []

        query = """
        SELECT id, rule_name, rule_type, conditions, service_code, description,
               priority, valid_from, valid_to, dmn_file_path
        FROM service_rules
        WHERE is_active = true
        AND (valid_from <= CURRENT_TIMESTAMP)
        AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
        """

        params = []
        if rule_type:
            query += " AND rule_type = $1"
            params.append(rule_type)

        query += " ORDER BY priority ASC, valid_from DESC"

        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    async def get_customer_pricing(self, customer_id: str, weight_class: str,
                                   transport_direction: str) -> Optional[Dict[str, Any]]:
        """Get customer-specific pricing with offer-based lookup"""
        if self.connection_pool is None:
            logger.warning("Database not available - customer pricing lookup skipped")
            return None

        query = """
        SELECT id, customer_id, offer_code, weight_class, transport_direction,
               route_from, route_to, price, minimum_price, currency, unit,
               valid_from, valid_to
        FROM main_service_prices
        WHERE customer_id = $1
        AND weight_class = $2
        AND transport_direction = $3
        AND is_active = true
        AND (valid_from <= CURRENT_TIMESTAMP)
        AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
        ORDER BY valid_from DESC
        LIMIT 1
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, customer_id, weight_class, transport_direction)
            if row:
                return dict(row)
            return None

    async def get_fallback_pricing(self, weight_class: str, transport_direction: str) -> Optional[Dict[str, Any]]:
        """Get fallback pricing when customer-specific pricing is not available"""
        if self.connection_pool is None:
            logger.warning("Database not available - fallback pricing lookup skipped")
            return None

        query = """
        SELECT id, offer_code, weight_class, transport_direction,
               price, minimum_price, currency, unit
        FROM main_service_prices
        WHERE customer_id IS NULL  -- Generic pricing
        AND weight_class = $1
        AND transport_direction = $2
        AND is_active = true
        AND (valid_from <= CURRENT_TIMESTAMP)
        AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
        ORDER BY valid_from DESC
        LIMIT 1
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, weight_class, transport_direction)
            if row:
                return dict(row)
            return None

    async def get_additional_service_pricing(self, service_code: str) -> Optional[Dict[str, Any]]:
        """Get pricing for additional services"""
        if self.connection_pool is None:
            logger.warning("Database not available - additional service pricing lookup skipped")
            return None

        query = """
        SELECT id, service_code, service_name, price_type, price, currency,
               valid_from, valid_to
        FROM additional_service_prices
        WHERE service_code = $1
        AND is_active = true
        AND (valid_from <= CURRENT_TIMESTAMP)
        AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
        ORDER BY valid_from DESC
        LIMIT 1
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, service_code)
            if row:
                return dict(row)
            return None

    async def get_customer_by_code(self, customer_code: str) -> Optional[Dict[str, Any]]:
        """Get customer information by code"""
        if self.connection_pool is None:
            logger.warning(f"Database not available - customer lookup skipped for {customer_code}")
            return None

        query = """
        SELECT id, code, name, customer_group, vat_id, country_code
        FROM customers
        WHERE code = $1 AND is_active = true
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, customer_code)
            if row:
                return dict(row)
            return None

    async def apply_service_determination_rules(self, service_context: Dict[str, Any]) -> List[str]:
        """Apply service determination rules based on context"""
        if self.connection_pool is None:
            logger.warning("Database not available - returning empty service determination rules")
            return []

        # This implements the 8 service determination rules from the roadmap

        rules_query = """
        SELECT service_code, conditions, priority
        FROM service_rules
        WHERE rule_type = 'SERVICE_DETERMINATION'
        AND is_active = true
        AND (valid_from <= CURRENT_TIMESTAMP)
        AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
        ORDER BY priority ASC
        """

        async with self.connection_pool.acquire() as conn:
            rules = await conn.fetch(rules_query)

            applicable_services = []

            for rule in rules:
                conditions = rule['conditions']
                service_code = rule['service_code']

                # Evaluate rule conditions against service context
                if self._evaluate_rule_conditions(conditions, service_context):
                    applicable_services.append(service_code)

            return applicable_services

    def _evaluate_rule_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate if rule conditions match the service context"""
        try:
            # Rule 1: KV + Dangerous + Date Range
            if (conditions.get('transport_type') == 'KV' and
                conditions.get('dangerous_goods') and
                'date_range' in conditions):

                date_range = conditions['date_range']
                departure_date = datetime.fromisoformat(context.get('departure_date', ''))
                from_date = datetime.fromisoformat(date_range['from'])
                to_date = datetime.fromisoformat(date_range['to'])

                return (context.get('transport_type') == 'KV' and
                        context.get('dangerous_goods') and
                        from_date <= departure_date <= to_date)

            # Rule 2: Main + KV + Dangerous
            if (conditions.get('service_type') == 'MAIN' and
                conditions.get('transport_type') == 'KV' and
                conditions.get('dangerous_goods')):

                return (context.get('service_type') == 'MAIN' and
                        context.get('transport_type') == 'KV' and
                        context.get('dangerous_goods'))

            # Rule 3: Main + KV
            if (conditions.get('service_type') == 'MAIN' and
                conditions.get('transport_type') == 'KV'):

                return (context.get('service_type') == 'MAIN' and
                        context.get('transport_type') == 'KV')

            # Rule 4: Main (generic)
            if conditions.get('service_type') == 'MAIN':
                return context.get('service_type') == 'MAIN'

            # Rule 5: Trucking (generic)
            if conditions.get('service_type') == 'TRUCKING':
                return context.get('service_type') == 'TRUCKING'

            # Rule 6: Station-specific security
            if 'station_codes' in conditions:
                station_codes = conditions['station_codes']
                departure_station = context.get('departure_station')
                return departure_station in station_codes

            # Rule 7: Customs
            if (conditions.get('customs_type') and
                conditions.get('country')):
                return (context.get('customs_type') == conditions['customs_type'] and
                        context.get('country') == conditions['country'])

            # Rule 8: Additional services
            if conditions.get('additional_services', {}).get('exists'):
                return context.get('has_additional_services', False)

            return False

        except Exception as e:
            logger.warning(f"Rule condition evaluation failed: {e}")
            return False

# Global database connection instance
rating_db = RatingDatabaseConnection()