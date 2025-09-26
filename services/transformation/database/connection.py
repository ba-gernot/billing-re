import os
import asyncpg
from typing import Optional, Dict, Any, List
from loguru import logger
import json

class DatabaseConnection:
    """Database connection manager for transformation service"""

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
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Database connection pool closed")

    async def get_container_type(self, iso_code: str) -> Optional[Dict[str, Any]]:
        """Get container type information by ISO code"""
        query = """
        SELECT iso_code, length_ft, tare_weight_kg, max_payload_kg, max_gross_weight_kg
        FROM container_types
        WHERE iso_code = $1 AND is_active = true
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, iso_code)
            if row:
                return dict(row)
            return None

    async def get_customer(self, customer_code: str) -> Optional[Dict[str, Any]]:
        """Get customer information by code"""
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

    async def insert_operational_order(self, order_data: Dict[str, Any]) -> str:
        """Insert operational order and return ID"""
        query = """
        INSERT INTO operational_orders (
            order_reference, customer_id, freightpayer_id, departure_date,
            transport_direction, container_data, route_data, trucking_data,
            dangerous_goods_flag, raw_input
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id
        """

        async with self.connection_pool.acquire() as conn:
            # This is a simplified version - in real implementation we'd need to:
            # 1. Lookup customer_id and freightpayer_id from codes
            # 2. Parse and structure the JSON data properly

            row = await conn.fetchrow(
                query,
                order_data.get("order_reference"),
                "00000000-0000-0000-0000-000000000001",  # Placeholder customer_id
                "00000000-0000-0000-0000-000000000002",  # Placeholder freightpayer_id
                order_data.get("departure_date"),
                order_data.get("transport_direction"),
                json.dumps(order_data.get("container_data", {})),
                json.dumps(order_data.get("route_data", {})),
                json.dumps(order_data.get("trucking_data", {})),
                order_data.get("dangerous_goods_flag", False),
                json.dumps(order_data)
            )

            return str(row["id"])

    async def insert_service_orders(self, service_orders: List[Dict[str, Any]]) -> List[str]:
        """Insert service orders and return IDs"""
        query = """
        INSERT INTO service_orders (
            operational_order_id, service_type, service_code, description,
            quantity, weight_class, route_from, route_to, loading_status,
            transport_type, service_data
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        RETURNING id
        """

        inserted_ids = []
        async with self.connection_pool.acquire() as conn:
            for order in service_orders:
                row = await conn.fetchrow(
                    query,
                    order.get("operational_order_id"),
                    order.get("service_type"),
                    order.get("service_code"),
                    order.get("description"),
                    order.get("quantity", 1),
                    order.get("weight_class"),
                    order.get("route_from"),
                    order.get("route_to"),
                    order.get("loading_status"),
                    order.get("transport_type"),
                    json.dumps(order.get("service_data", {}))
                )
                inserted_ids.append(str(row["id"]))

        return inserted_ids

# Global database connection instance
db = DatabaseConnection()