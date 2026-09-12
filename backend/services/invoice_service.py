"""
MegaCommerce Local Invoice Generation Engine
Zero External API Key Compliance Architecture
Generates Local PDF & HTML Printable Invoices using ReportLab
"""

import os
import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from sqlalchemy.orm import Session
from database.models.order import Order
from shared.exceptions import ResourceNotFoundError
from config.settings import settings


class LocalInvoiceService:
    """Generates locally downloadable PDF & HTML invoices."""

    def __init__(self, db: Session):
        self.db = db
        self.storage_dir = settings.simulators.INVOICE_STORAGE_DIR

    def generate_pdf_invoice(self, order_id: str) -> Path:
        """Generates a styled PDF invoice document on disk."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise ResourceNotFoundError("Order", order_id)

        file_path = self.storage_dir / f"Invoice_{order.order_number}.pdf"
        
        doc = SimpleDocTemplate(str(file_path), pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e293b")
        )

        elements = []

        # Header
        elements.append(Paragraph(f"<b>MEGACOMMERCE ECOSYSTEM</b>", title_style))
        elements.append(Paragraph(f"Official Sales Invoice — #{order.order_number}", styles['Heading2']))
        elements.append(Spacer(1, 12))

        # Meta Info Table
        meta_data = [
            ["Invoice Date:", datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"), "Payment Method:", order.payment_method],
            ["Order Status:", order.order_status, "Payment Status:", order.payment_status],
            ["Customer ID:", order.customer_id[:8], "Tracking No:", order.tracking_number or "N/A"]
        ]
        meta_table = Table(meta_data, colWidths=[100, 180, 100, 160])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#334155")),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 16))

        # Line Items Table
        items_data = [["Product Title", "SKU", "Unit Price", "Qty", "Total Price"]]
        for item in order.items:
            items_data.append([
                item.product_title[:30],
                item.sku[:15],
                f"${item.unit_price:.2f}",
                str(item.quantity),
                f"${item.total_price:.2f}"
            ])

        # Summary rows
        items_data.append(["", "", "", "Subtotal:", f"${order.subtotal:.2f}"])
        items_data.append(["", "", "", "Discount:", f"-${order.discount_amount:.2f}"])
        items_data.append(["", "", "", "Tax (8%):", f"${order.tax_amount:.2f}"])
        items_data.append(["", "", "", "Shipping:", f"${order.shipping_amount:.2f}"])
        items_data.append(["", "", "", "Grand Total:", f"${order.total_amount:.2f}"])

        items_table = Table(items_data, colWidths=[200, 100, 80, 60, 100])
        items_table.setStyle(TableStyle([
            ('HEADERBACKGROUND', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('HEADERTEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-6), 0.5, colors.HexColor("#cbd5e1")),
            ('LINEBELOW', (0,-5), (-1,-1), 1, colors.HexColor("#0f172a")),
            ('FONTNAME', (3,-1), (-1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 24))
        elements.append(Paragraph("Thank you for shopping with MegaCommerce! All purchases are simulated for demonstration.", styles['Italic']))

        doc.build(elements)
        return file_path
