from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
import time
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import os
from pathlib import Path

from database.connection import billing_db
from generation.pdf_generator import InvoicePDFGenerator
from xlsx_tax_processor import XLSXTaxProcessor
import logging

logger = logging.getLogger(__name__)

# Initialize XLSX tax processor with symlink path to shared rules
current_dir = Path(__file__).parent
rules_dir = current_dir / "shared" / "rules"
tax_processor = XLSXTaxProcessor(rules_dir=rules_dir)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await billing_db.initialize()
    yield
    # Shutdown
    await billing_db.close()

app = FastAPI(
    title="Billing Service",
    description="Advanced invoice generation with tax calculation and document aggregation",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize PDF generator
pdf_generator = InvoicePDFGenerator()


class BillingLineItem(BaseModel):
    service_code: str
    service_name: str
    description: str
    quantity: int = 1
    unit_price: float
    total_price: float
    offer_code: Optional[str] = None
    price_source: Optional[str] = None


class BillingInput(BaseModel):
    order_reference: str
    customer_code: str
    transport_direction: str
    route_from: Optional[str] = None
    route_to: Optional[str] = None
    departure_date: Optional[str] = None
    line_items: List[BillingLineItem]
    operational_order_id: Optional[str] = None
    # Tax calculation fields
    departure_country: Optional[str] = "DE"
    destination_country: Optional[str] = None
    vat_id: Optional[str] = None
    customs_procedure: Optional[str] = None
    loading_status: Optional[str] = "beladen"


class TaxCalculationResult(BaseModel):
    tax_case: str
    tax_rate: float
    tax_amount: float
    tax_description: str
    applicable_rule: Optional[str] = None


class DocumentAggregationResult(BaseModel):
    grouped_items: List[BillingLineItem]
    consolidation_summary: Dict[str, Any]  # Allow int and float for consolidation_ratio
    total_services: int


class InvoiceResult(BaseModel):
    invoice_id: str
    invoice_number: str
    customer_code: str
    customer_name: Optional[str] = None
    invoice_date: str
    due_date: str
    subtotal: float
    tax_calculation: TaxCalculationResult
    total: float
    currency: str = "EUR"
    line_items: List[BillingLineItem]
    document_aggregation: DocumentAggregationResult
    pdf_path: Optional[str] = None
    xml_path: Optional[str] = None
    status: str = "draft"
    processing_details: Dict = {}
    warnings: List[str] = []


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "billing"}


@app.post("/generate-invoice", response_model=InvoiceResult)
async def generate_invoice(billing_input: BillingInput):
    """
    Advanced invoice generation with database-driven tax calculation and document aggregation

    Process:
    1. Document aggregation and consolidation
    2. Database-driven tax calculation (3 scenarios)
    3. Generate sequential invoice number
    4. Persist billing documents to database
    5. Create comprehensive invoice result
    6. Generate PDF and XML (planned)
    """
    start_time = time.time()
    warnings = []

    try:
        # Step 1: Get customer information
        customer_data = await billing_db.get_customer_by_code(billing_input.customer_code)
        if not customer_data:
            warnings.append(f"Customer {billing_input.customer_code} not found in database")
            customer_data = {"id": None, "name": billing_input.customer_code}

        # Step 2: Document aggregation and consolidation
        aggregation_result = await _aggregate_documents(billing_input.line_items)

        # Step 3: Calculate subtotal
        subtotal = sum(item.total_price for item in aggregation_result.grouped_items)

        # Step 4: Advanced tax calculation using XLSX rules
        tax_calculation = await _calculate_advanced_tax(
            billing_input.transport_direction,
            subtotal,
            customer_data,
            warnings,
            billing_input  # Pass full input for XLSX processor
        )

        # Step 5: Calculate total
        total = subtotal + tax_calculation.tax_amount

        # Step 6: Generate sequential invoice number
        invoice_number = await billing_db.generate_invoice_number()

        # Step 7: Prepare file paths
        pdf_path = f"/invoices/{invoice_number}.pdf"
        xml_path = f"/invoices/{invoice_number}.xml"

        # Step 8: Create invoice ID
        invoice_id = f"INV-{datetime.now().strftime('%Y%m%d')}-{invoice_number.split('-')[1]}"

        # Step 9: Persist billing documents to database
        billing_documents = []
        for item in aggregation_result.grouped_items:
            billing_doc = {
                "service_order_id": None,  # Would link to service orders from transformation
                "offer_id": item.offer_code,
                "base_price": item.unit_price,
                "calculated_amount": item.total_price,
                "currency": "EUR",
                "tax_case": tax_calculation.tax_case,
                "tax_rate": tax_calculation.tax_rate,
                "tax_amount": (item.total_price * tax_calculation.tax_rate),
                "total_amount": item.total_price * (1 + tax_calculation.tax_rate),
                "pricing_details": {
                    "service_code": item.service_code,
                    "price_source": item.price_source,
                    "quantity": item.quantity
                }
            }
            billing_documents.append(billing_doc)

        # Insert billing documents
        try:
            billing_doc_ids = await billing_db.insert_billing_documents(billing_documents)
        except Exception as e:
            warnings.append(f"Failed to persist billing documents: {e}")
            billing_doc_ids = []

        # Step 10: Persist invoice document
        invoice_data = {
            "invoice_number": invoice_number,
            "operational_order_id": billing_input.operational_order_id,
            "customer_id": customer_data.get("id"),
            "subtotal": subtotal,
            "total_tax": tax_calculation.tax_amount,
            "total_amount": total,
            "currency": "EUR",
            "invoice_date": datetime.now(),
            "due_date": datetime.now() + timedelta(days=30),
            "pdf_path": pdf_path,
            "xml_path": xml_path,
            "status": "draft",
            "metadata": {
                "billing_doc_ids": billing_doc_ids,
                "transport_direction": billing_input.transport_direction,
                "route": {
                    "from": billing_input.route_from,
                    "to": billing_input.route_to
                },
                "processing_time_ms": (time.time() - start_time) * 1000
            }
        }

        try:
            invoice_db_id = await billing_db.insert_invoice_document(invoice_data)
        except Exception as e:
            warnings.append(f"Failed to persist invoice document: {e}")
            invoice_db_id = None

        # Step 11: Generate PDF invoice using ReportLab
        try:
            generated_pdf_path = await pdf_generator.generate_invoice_pdf(
                invoice_data=invoice_data,
                line_items=[item.dict() for item in aggregation_result.grouped_items],
                tax_calculation=tax_calculation.dict(),
                output_path=pdf_path
            )
            logger.info(f"PDF invoice generated: {generated_pdf_path}")
        except Exception as e:
            warnings.append(f"PDF generation failed: {e}")
            logger.error(f"PDF generation error: {e}")

        # Step 12: Generate XML (placeholder - would use ZUGFeRD format)
        # await _generate_xml_invoice(invoice_data, xml_path)

        # Create comprehensive result
        invoice_result = InvoiceResult(
            invoice_id=invoice_id,
            invoice_number=invoice_number,
            customer_code=billing_input.customer_code,
            customer_name=customer_data.get("name"),
            invoice_date=datetime.now().isoformat(),
            due_date=(datetime.now() + timedelta(days=30)).isoformat(),
            subtotal=subtotal,
            tax_calculation=tax_calculation,
            total=total,
            currency="EUR",
            line_items=aggregation_result.grouped_items,
            document_aggregation=aggregation_result,
            pdf_path=pdf_path,
            xml_path=xml_path,
            status="draft",
            processing_details={
                "processing_time_ms": (time.time() - start_time) * 1000,
                "invoice_db_id": invoice_db_id,
                "billing_doc_count": len(billing_doc_ids)
            },
            warnings=warnings
        )

        return invoice_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Invoice generation failed: {str(e)}")


async def _aggregate_documents(line_items: List[BillingLineItem]) -> DocumentAggregationResult:
    """
    Aggregate and consolidate billing documents using roadmap business rules

    Business Rules:
    1. Group identical services together
    2. Consolidate quantities where applicable
    3. Maintain service-specific pricing
    4. Track consolidation statistics
    """

    # Group items by service code for consolidation
    service_groups = {}

    for item in line_items:
        key = (item.service_code, item.unit_price, item.offer_code)

        if key in service_groups:
            # Consolidate quantity and total
            existing = service_groups[key]
            existing.quantity += item.quantity
            existing.total_price += item.total_price
        else:
            # Create new consolidated item
            service_groups[key] = BillingLineItem(
                service_code=item.service_code,
                service_name=item.service_name,
                description=f"{item.description} (consolidated)",
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                offer_code=item.offer_code,
                price_source=item.price_source
            )

    grouped_items = list(service_groups.values())

    # Create consolidation summary
    consolidation_summary = {
        "original_items": len(line_items),
        "consolidated_items": len(grouped_items),
        "consolidation_ratio": len(grouped_items) / len(line_items) if line_items else 0,
        "total_quantity": sum(item.quantity for item in grouped_items)
    }

    return DocumentAggregationResult(
        grouped_items=grouped_items,
        consolidation_summary=consolidation_summary,
        total_services=len(grouped_items)
    )


async def _calculate_advanced_tax(transport_direction: str, subtotal: float,
                                 customer_data: Dict, warnings: List[str],
                                 billing_input: BillingInput = None) -> TaxCalculationResult:
    """
    Advanced tax calculation using XLSX rules for 3 scenarios from roadmap:
    1. Export: 0% VAT (§4 No. 3a UStG)
    2. Import: Reverse charge mechanism
    3. Domestic: 19% German VAT

    Primary: XLSX processor (shared/rules/3_1_Regeln_Steuerberechnung.xlsx)
    Fallback: Database rules or hardcoded rules
    """

    # Get customer country for tax context
    customer_country = customer_data.get("country_code", "DE")

    # Try XLSX processor first
    if billing_input:
        try:
            destination_country = billing_input.destination_country or customer_country
            tax_result = tax_processor.calculate_tax_for_transport(
                transport_direction=transport_direction,
                departure_country=billing_input.departure_country or "DE",
                destination_country=destination_country,
                vat_id=billing_input.vat_id,
                customs_procedure=billing_input.customs_procedure,
                loading_status=billing_input.loading_status or "beladen"
            )

            if tax_result:
                logger.info(f"Tax calculated via XLSX: {tax_result['tax_case']} ({tax_result['rule_matched']})")

                # Map XLSX result to TaxCalculationResult
                tax_amount = subtotal * tax_result['tax_rate']

                # Build description
                description_parts = [tax_result['tax_case']]
                if tax_result.get('sap_vat_indicator'):
                    description_parts.append(f"SAP: {tax_result['sap_vat_indicator']}")

                return TaxCalculationResult(
                    tax_case=tax_result['tax_case'],
                    tax_rate=tax_result['tax_rate'],
                    tax_amount=tax_amount,
                    tax_description=' - '.join(description_parts),
                    applicable_rule=f"XLSX Rule ({tax_result['rule_matched']})"
                )
        except Exception as e:
            logger.warning(f"XLSX tax processor failed: {e}", exc_info=True)
            warnings.append(f"XLSX tax processor failed: {e}")

    # Fallback: Try database-driven tax rule lookup
    try:
        tax_rule = await billing_db.get_tax_rules(
            transport_direction=transport_direction,
            from_country=billing_input.departure_country or "DE",  # Use passed country (not hardcoded)
            to_country=customer_country
        )

        if tax_rule:
            # Use database rule
            tax_case = tax_rule["tax_case"]
            tax_rate = float(tax_rule["tax_rate"])
            tax_description = tax_rule["description"]
            applicable_rule = tax_rule["rule_name"]
            tax_amount = subtotal * tax_rate

            logger.info(f"Tax calculated via database: {tax_case}")

            return TaxCalculationResult(
                tax_case=tax_case,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                tax_description=tax_description,
                applicable_rule=f"Database Rule: {applicable_rule}"
            )
    except Exception as e:
        logger.warning(f"Database tax lookup failed: {e}")
        warnings.append(f"Database tax lookup failed: {e}")

    # Final fallback to hardcoded roadmap rules
    warnings.append("Using hardcoded fallback tax rules")
    logger.warning("Using hardcoded fallback tax rules")

    if transport_direction == "Export":
        tax_case = "§4 No. 3a UStG"
        tax_rate = 0.0
        tax_description = "Export transactions VAT exempt according to German tax law"
        applicable_rule = "Export VAT Exemption (fallback)"
    elif transport_direction == "Import":
        tax_case = "Reverse charge"
        tax_rate = 0.0
        tax_description = "Import reverse charge mechanism - VAT handled by recipient"
        applicable_rule = "Import Reverse Charge (fallback)"
    else:  # Domestic
        tax_case = "Standard VAT"
        tax_rate = 0.19
        tax_description = "Domestic German VAT 19%"
        applicable_rule = "Domestic Standard VAT (fallback)"

    # Calculate tax amount
    tax_amount = subtotal * tax_rate

    return TaxCalculationResult(
        tax_case=tax_case,
        tax_rate=tax_rate,
        tax_amount=tax_amount,
        tax_description=tax_description,
        applicable_rule=applicable_rule
    )


# Legacy functions (kept for backward compatibility)
def _determine_tax_case(transport_direction: str) -> Dict[str, any]:
    """Legacy tax determination (replaced by database rules)"""
    tax_cases = {
        "Export": {"case": "§4 No. 3a UStG", "rate": 0.0},
        "Import": {"case": "Reverse charge", "rate": 0.0},
        "Domestic": {"case": "Standard VAT", "rate": 0.19}
    }
    return tax_cases.get(transport_direction, {"case": "Standard VAT", "rate": 0.19})


def _generate_invoice_number() -> str:
    """Legacy invoice number generation (replaced by database sequence)"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"INV-{timestamp}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3003)