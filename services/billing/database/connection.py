import os
import asyncpg
from typing import Optional, Dict, Any, List
from loguru import logger
import json
from datetime import datetime

class BillingDatabaseConnection:
    """Database connection manager for billing service with tax and document management"""

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
            logger.info("Billing service database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise

    async def close(self):
        """Close database connection pool"""
        if self.connection_pool:
            await self.connection_pool.close()
            logger.info("Billing service database connection pool closed")

    async def get_tax_rules(self, transport_direction: str, from_country: str = "DE",
                           to_country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get applicable tax rules based on transport direction and countries"""
        query = """
        SELECT id, rule_name, conditions, tax_case, tax_rate, description,
               valid_from, valid_to
        FROM tax_rules
        WHERE is_active = true
        AND (valid_from <= CURRENT_TIMESTAMP)
        AND (valid_to IS NULL OR valid_to >= CURRENT_TIMESTAMP)
        ORDER BY valid_from DESC
        """

        async with self.connection_pool.acquire() as conn:
            rows = await conn.fetch(query)

            for row in rows:
                conditions = row['conditions']

                # Evaluate tax rule conditions
                if self._evaluate_tax_conditions(conditions, transport_direction, from_country, to_country):
                    return dict(row)

            return None

    def _evaluate_tax_conditions(self, conditions: Dict[str, Any], transport_direction: str,
                                 from_country: str, to_country: Optional[str]) -> bool:
        """Evaluate if tax rule conditions match the transport context"""
        try:
            # Export VAT exemption
            if (conditions.get('transport_direction') == 'Export' and
                conditions.get('from_country') == from_country and
                transport_direction == 'Export'):
                return True

            # Import reverse charge
            if (conditions.get('transport_direction') == 'Import' and
                conditions.get('to_country') == to_country and
                transport_direction == 'Import'):
                return True

            # Domestic VAT
            if (conditions.get('transport_direction') == 'Domestic' and
                conditions.get('from_country') == from_country and
                conditions.get('to_country') == to_country and
                transport_direction == 'Domestic'):
                return True

            # EU transport
            if (conditions.get('transport_direction') == 'Export' and
                conditions.get('from_country') == from_country and
                conditions.get('to_eu') and
                transport_direction == 'Export'):
                # Would need EU country lookup here
                return False  # Simplified for now

            return False

        except Exception as e:
            logger.warning(f"Tax condition evaluation failed: {e}")
            return False

    async def insert_billing_documents(self, billing_data: List[Dict[str, Any]]) -> List[str]:
        """Insert billing documents and return IDs"""
        query = """
        INSERT INTO billing_documents (
            service_order_id, offer_id, base_price, calculated_amount, currency,
            tax_case, tax_rate, tax_amount, total_amount, pricing_details
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        RETURNING id
        """

        inserted_ids = []
        async with self.connection_pool.acquire() as conn:
            for billing in billing_data:
                row = await conn.fetchrow(
                    query,
                    billing.get("service_order_id"),
                    billing.get("offer_id"),
                    billing.get("base_price"),
                    billing.get("calculated_amount"),
                    billing.get("currency", "EUR"),
                    billing.get("tax_case"),
                    billing.get("tax_rate"),
                    billing.get("tax_amount"),
                    billing.get("total_amount"),
                    json.dumps(billing.get("pricing_details", {}))
                )
                inserted_ids.append(str(row["id"]))

        return inserted_ids

    async def generate_invoice_number(self) -> str:
        """Generate sequential invoice number"""
        query = """
        SELECT COALESCE(MAX(CAST(SUBSTRING(invoice_number FROM 'INV-(.*)') AS INTEGER)), 0) + 1 as next_number
        FROM invoice_documents
        WHERE invoice_number LIKE 'INV-%'
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query)
            next_number = row['next_number']
            return f"INV-{next_number:06d}"

    async def insert_invoice_document(self, invoice_data: Dict[str, Any]) -> str:
        """Insert invoice document and return ID"""
        query = """
        INSERT INTO invoice_documents (
            invoice_number, operational_order_id, customer_id, subtotal,
            total_tax, total_amount, currency, invoice_date, due_date,
            pdf_path, xml_path, status, metadata
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        RETURNING id
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(
                query,
                invoice_data.get("invoice_number"),
                invoice_data.get("operational_order_id"),
                invoice_data.get("customer_id"),
                invoice_data.get("subtotal"),
                invoice_data.get("total_tax"),
                invoice_data.get("total_amount"),
                invoice_data.get("currency", "EUR"),
                invoice_data.get("invoice_date"),
                invoice_data.get("due_date"),
                invoice_data.get("pdf_path"),
                invoice_data.get("xml_path"),
                invoice_data.get("status", "draft"),
                json.dumps(invoice_data.get("metadata", {}))
            )
            return str(row["id"])

    async def get_customer_by_code(self, customer_code: str) -> Optional[Dict[str, Any]]:
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

    async def get_country_info(self, country_code: str) -> Optional[Dict[str, Any]]:
        """Get country information including VAT rates"""
        query = """
        SELECT code, name, eu_member, default_vat_rate, currency
        FROM countries
        WHERE code = $1 AND is_active = true
        """

        async with self.connection_pool.acquire() as conn:
            row = await conn.fetchrow(query, country_code)
            if row:
                return dict(row)
            return None

# Global database connection instance
billing_db = BillingDatabaseConnection()