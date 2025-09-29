import os
from typing import Dict, Any, List
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.platypus.flowables import HRFlowable
import logging

logger = logging.getLogger(__name__)

class InvoicePDFGenerator:
    """Professional PDF invoice generator using ReportLab"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.page_width, self.page_height = A4

        # Custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=20,
            spaceAfter=30,
            textColor=colors.darkblue
        )

        self.header_style = ParagraphStyle(
            'CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )

    async def generate_invoice_pdf(self, invoice_data: Dict[str, Any],
                                   line_items: List[Dict[str, Any]],
                                   tax_calculation: Dict[str, Any],
                                   output_path: str) -> str:
        """
        Generate professional PDF invoice based on German standards

        Args:
            invoice_data: Invoice header information
            line_items: List of billing line items
            tax_calculation: Tax calculation results
            output_path: Output file path

        Returns:
            Generated PDF file path
        """

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=inch,
                leftMargin=inch,
                topMargin=inch,
                bottomMargin=inch
            )

            # Build content
            story = []

            # Company header
            story.extend(self._build_company_header())
            story.append(Spacer(1, 20))

            # Customer information
            story.extend(self._build_customer_section(invoice_data))
            story.append(Spacer(1, 20))

            # Invoice header
            story.extend(self._build_invoice_header(invoice_data))
            story.append(Spacer(1, 20))

            # Line items table
            story.extend(self._build_line_items_table(line_items))
            story.append(Spacer(1, 20))

            # Totals section
            story.extend(self._build_totals_section(invoice_data, tax_calculation))
            story.append(Spacer(1, 20))

            # Tax information
            story.extend(self._build_tax_section(tax_calculation))
            story.append(Spacer(1, 20))

            # Footer
            story.extend(self._build_footer())

            # Generate PDF
            doc.build(story)

            logger.info(f"Invoice PDF generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"PDF generation failed: {e}")
            raise

    def _build_company_header(self) -> List:
        """Build company header section"""
        elements = []

        # Company logo placeholder
        elements.append(Paragraph("🚚 BILLING RE SYSTEM", self.title_style))

        # Company details
        company_info = """
        <b>Transport & Logistics Billing Solutions</b><br/>
        Musterstraße 123<br/>
        20095 Hamburg, Germany<br/>
        Tel: +49 40 123456<br/>
        Email: billing@transport-re.com<br/>
        USt-IdNr.: DE123456789
        """
        elements.append(Paragraph(company_info, self.styles['Normal']))
        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))

        return elements

    def _build_customer_section(self, invoice_data: Dict[str, Any]) -> List:
        """Build customer address section"""
        elements = []

        elements.append(Paragraph("Rechnungsempfänger / Bill To:", self.header_style))

        customer_info = f"""
        <b>{invoice_data.get('customer_name', invoice_data['customer_code'])}</b><br/>
        Customer Code: {invoice_data['customer_code']}<br/>
        [Customer Address would be loaded from database]<br/>
        """

        elements.append(Paragraph(customer_info, self.styles['Normal']))

        return elements

    def _build_invoice_header(self, invoice_data: Dict[str, Any]) -> List:
        """Build invoice header with key information"""
        elements = []

        elements.append(Paragraph("RECHNUNG / INVOICE", self.title_style))

        # Invoice details table
        invoice_details = [
            ['Rechnungsnummer / Invoice Number:', invoice_data['invoice_number']],
            ['Rechnungsdatum / Invoice Date:', invoice_data['invoice_date'][:10]],
            ['Fälligkeitsdatum / Due Date:', invoice_data['due_date'][:10]],
            ['Währung / Currency:', invoice_data['currency']],
            ['Order Reference:', invoice_data.get('order_reference', 'N/A')]
        ]

        table = Table(invoice_details, colWidths=[3*inch, 2*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ]))

        elements.append(table)

        return elements

    def _build_line_items_table(self, line_items: List[Dict[str, Any]]) -> List:
        """Build detailed line items table"""
        elements = []

        elements.append(Paragraph("Leistungen / Services:", self.header_style))

        # Table headers
        headers = [
            'Service Code',
            'Beschreibung / Description',
            'Menge / Qty',
            'Einzelpreis / Unit Price',
            'Gesamtpreis / Total'
        ]

        # Prepare table data
        table_data = [headers]

        for item in line_items:
            row = [
                item.get('service_code', ''),
                item.get('description', ''),
                str(item.get('quantity', 1)),
                f"€{item.get('unit_price', 0):.2f}",
                f"€{item.get('total_price', 0):.2f}"
            ]
            table_data.append(row)

        # Create table
        table = Table(table_data, colWidths=[1*inch, 3*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            # Header formatting
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),

            # Data formatting
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),  # Right-align numbers
            ('ALIGN', (0, 1), (1, -1), 'LEFT'),    # Left-align text

            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))

        elements.append(table)

        return elements

    def _build_totals_section(self, invoice_data: Dict[str, Any],
                             tax_calculation: Dict[str, Any]) -> List:
        """Build totals calculation section"""
        elements = []

        # Totals table
        totals_data = [
            ['Zwischensumme / Subtotal:', f"€{invoice_data['subtotal']:.2f}"],
            ['MwSt. / VAT:', f"€{tax_calculation['tax_amount']:.2f}"],
            ['', ''],  # Separator line
            ['Gesamtbetrag / Total:', f"€{invoice_data['total']:.2f}"]
        ]

        table = Table(totals_data, colWidths=[4*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (0, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.darkblue),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ]))

        elements.append(table)

        return elements

    def _build_tax_section(self, tax_calculation: Dict[str, Any]) -> List:
        """Build tax information section"""
        elements = []

        elements.append(Paragraph("Steuerliche Hinweise / Tax Information:", self.header_style))

        tax_info = f"""
        <b>Steuerfall / Tax Case:</b> {tax_calculation['tax_case']}<br/>
        <b>Steuersatz / Tax Rate:</b> {tax_calculation['tax_rate']*100:.1f}%<br/>
        <b>Beschreibung / Description:</b> {tax_calculation['tax_description']}<br/>
        """

        if tax_calculation.get('applicable_rule'):
            tax_info += f"<b>Angewandte Regel / Applied Rule:</b> {tax_calculation['applicable_rule']}<br/>"

        elements.append(Paragraph(tax_info, self.styles['Normal']))

        return elements

    def _build_footer(self) -> List:
        """Build invoice footer"""
        elements = []

        elements.append(HRFlowable(width="100%", thickness=1, lineCap='round', color=colors.darkblue))

        footer_text = f"""
        <b>Zahlungsbedingungen / Payment Terms:</b> 30 Tage netto / Net 30 days<br/>
        <b>Bankverbindung / Bank Details:</b> IBAN: DE89 1234 5678 9012 3456 78 | BIC: DEUTDEFF<br/>
        <br/>
        Geschäftsführer: Max Mustermann | Handelsregister: HRB 123456 Hamburg<br/>
        Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by Billing RE System<br/>
        <font size="8">🤖 Generated with Claude Code | https://claude.ai/code</font>
        """

        elements.append(Paragraph(footer_text, self.styles['Normal']))

        return elements


# Export the class for use in main billing service
__all__ = ['InvoicePDFGenerator']