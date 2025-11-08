#!/usr/bin/env python3
"""
PDF Invoice Generator

Generates 20 invoice PDFs in `generated_invoices/` folder. 5 are perfect invoices,
15 contain a variety of realistic anomalies for testing the validation and
duplication detection pipeline.

Dependencies: reportlab

Run: python3 pdf_report_generator.py
"""
import os
import re
import random
from decimal import Decimal, ROUND_HALF_UP
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle


OUT_DIR = "generated_invoices"
PERFECT_COUNT = 5
TOTAL_COUNT = 20


def money(v):
    return float(Decimal(v).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


def make_invoice_data(seed_idx, anomaly=None, reuse_invoice_num=None):
    """Create structured invoice data. anomaly is a dict specifying which issue to introduce."""
    # Base supplier / invoice info
    supplier = {
        "name": "INPRAVIA MINING RESOURCES PRIVATE LIMITED",
        "address": "C/22, Patel Park, Ranchi, India",
        "gstin": "20AAHCI0488C1Z1"
    }

    # Optionally reuse invoice number (for duplicates with different dates)
    if reuse_invoice_num:
        invoice_num = reuse_invoice_num
    else:
        invoice_num = f"IMR/25/GEN/{seed_idx:03d}"

    # Pick a date window
    base_date = f"2025-08-{(seed_idx%28)+1:02d}"

    # Create 4-7 line items
    items = []
    num_lines = random.choice([4,5,6,7])
    for i in range(num_lines):
        qty = random.choice([1,2,5,10,15,19,26])
        # unit price chosen to make taxable values reasonable
        unit_price = random.choice([1493.35, 877.96, 958.73, 249.27, 38827/26 if qty!=0 else 1000])
        unit_price = round(unit_price if unit_price>1 else unit_price*1000, 2)
        taxable_value = money(qty * unit_price)
        gst_rate = 18.0
        gst_amount = money(taxable_value * gst_rate / 100)

        items.append({
            "description": f"Service {i+1}",
            "hsn": random.choice(["999315","998519","170002715","190002421"]),
            "quantity": qty,
            "unit_price": unit_price,
            "taxable_value": taxable_value,
            "gst_rate": gst_rate,
            "gst_amount": gst_amount
        })

    # Base sums
    invoice_taxable = money(sum(it["taxable_value"] for it in items))
    invoice_tax = money(sum(it["gst_amount"] for it in items))
    invoice_total = money(invoice_taxable + invoice_tax)

    data = {
        "supplier": supplier,
        "invoice_num": invoice_num,
        "invoice_date": base_date,
        "line_items": items,
        "taxable_value": invoice_taxable,
        "total_tax": invoice_tax,
        "total_amount": invoice_total
    }

    # Introduce anomalies
    if anomaly:
        typ = anomaly.get("type")
        if typ == "arithmetic_error":
            # change one line taxable_value to an incorrect number (e.g., unit price missing a digit)
            idx = anomaly.get("line", 0) % len(items)
            wrong = money(items[idx]["taxable_value"] + random.choice([1,10,100,1000]))
            items[idx]["taxable_value"] = wrong
            # recalc invoice totals (intentionally inconsistent with qty*unit_price)
            data["taxable_value"] = money(sum(it["taxable_value"] for it in items))
            data["total_tax"] = money(sum(it["taxable_value"] * it["gst_rate"]/100 for it in items))
            data["total_amount"] = money(data["taxable_value"] + data["total_tax"])

        elif typ == "summation_error":
            # tamper top-level total tax or total_amount slightly
            data["total_tax"] = money(data["total_tax"] + random.choice([0.02, 0.1, 0.5, 1.0]))
            # leave line items unchanged -> mismatch

        elif typ == "quantity_duplication":
            # duplicate one line item with wrong quantity
            dup = items[0].copy()
            dup["quantity"] = dup["quantity"] + random.choice([1,2,5])
            dup["taxable_value"] = money(dup["quantity"] * dup["unit_price"])
            items.insert(0, dup)
            data["taxable_value"] = money(sum(it["taxable_value"] for it in items))
            data["total_tax"] = money(sum(it["taxable_value"] * it["gst_rate"]/100 for it in items))
            data["total_amount"] = money(data["taxable_value"] + data["total_tax"])

        elif typ == "wrong_tax_rate":
            # set wrong gst rate on one line
            idx = anomaly.get("line", 0) % len(items)
            items[idx]["gst_rate"] = random.choice([5.0, 12.0, 28.0])
            items[idx]["gst_amount"] = money(items[idx]["taxable_value"] * items[idx]["gst_rate"]/100)
            data["total_tax"] = money(sum(it["gst_amount"] for it in items))
            data["total_amount"] = money(data["taxable_value"] + data["total_tax"])

        elif typ == "same_invoice_diff_date":
            # keep same invoice number but change date
            data["invoice_date"] = anomaly.get("date", data["invoice_date"]) 

        elif typ == "logical_adjustment":
            # make small rounding differences across lines to create subtle mismatches
            for it in items:
                adjust = random.choice([-0.01, 0.01, 0.02])
                it["taxable_value"] = money(it["taxable_value"] + adjust)
            data["taxable_value"] = money(sum(it["taxable_value"] for it in items))
            data["total_tax"] = money(sum(it["taxable_value"] * it["gst_rate"]/100 for it in items))
            data["total_amount"] = money(data["taxable_value"] + data["total_tax"])

    return data


def draw_invoice_pdf(path, data):
    c = canvas.Canvas(path, pagesize=A4)
    w, h = A4

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(20*mm, h - 20*mm, "TAX INVOICE")

    # Supplier block
    c.setFont("Helvetica", 9)
    supplier = data["supplier"]
    c.drawString(20*mm, h - 28*mm, supplier["name"])
    c.drawString(20*mm, h - 32*mm, supplier["address"])
    c.drawString(20*mm, h - 36*mm, f"GSTIN: {supplier.get('gstin','N/A')}")

    # Invoice meta
    c.setFont("Helvetica-Bold", 10)
    c.drawString(120*mm, h - 28*mm, f"Invoice No.: {data['invoice_num']}")
    c.setFont("Helvetica", 9)
    c.drawString(120*mm, h - 33*mm, f"Dated: {data['invoice_date']}")

    # Line items table
    table_data = [["Sl. No", "Description", "HSN/SAC", "Qty", "Rate", "Taxable Amount (INR)", "GST %", "GST Amt"]]
    for i, it in enumerate(data["line_items"]):
        table_data.append([
            str(i+1),
            it["description"],
            it.get("hsn",""),
            str(it.get("quantity",0)),
            f"{it.get('unit_price',0):,.2f}",
            f"{it.get('taxable_value',0):,.2f}",
            f"{it.get('gst_rate',0):.2f}",
            f"{it.get('gst_amount',0):,.2f}"
        ])

    t = Table(table_data, colWidths=[15*mm, 55*mm, 22*mm, 15*mm, 22*mm, 30*mm, 15*mm, 22*mm])
    t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.25, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('ALIGN',(3,1),(-1,-1),'RIGHT'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('FONTSIZE', (0,0), (-1,-1), 8)
    ]))

    w_table, h_table = t.wrapOn(c, w-40*mm, h)
    t.drawOn(c, 20*mm, h - 110*mm - h_table)

    # Totals block
    totals_y = h - 120*mm - h_table
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(w - 20*mm, totals_y - 10*mm, f"Taxable Amount (INR): {data['taxable_value']:,.2f}")
    c.drawRightString(w - 20*mm, totals_y - 14*mm, f"Total Tax: {data['total_tax']:,.2f}")
    c.drawRightString(w - 20*mm, totals_y - 18*mm, f"Total Amount (INR): {data['total_amount']:,.2f}")

    # Footer note
    c.setFont("Helvetica", 7)
    c.drawString(20*mm, 20*mm, "This is a system generated invoice for testing - contains possible anomalies for validation testing.")

    c.showPage()
    c.save()


def generate_all():
    ensure_out_dir()

    # Plan anomalies for the 15 faulty invoices
    anomaly_types = [
        "arithmetic_error",
        "summation_error",
        "quantity_duplication",
        "wrong_tax_rate",
        "same_invoice_diff_date",
        "logical_adjustment"
    ]

    # create 5 perfect invoices
    generated = []
    for i in range(1, PERFECT_COUNT+1):
        data = make_invoice_data(i)
        fname = f"invoice_perfect_{i:02d}.pdf"
        path = os.path.join(OUT_DIR, fname)
        draw_invoice_pdf(path, data)
        generated.append(path)

    # For duplicates (same invoice diff dates) pick one invoice number to reuse
    reused_invoice_num = f"IMR/25/GEN/DUPE01"

    # Create the remaining invoices with anomalies
    for idx in range(PERFECT_COUNT+1, TOTAL_COUNT+1):
        # pick anomaly
        typ = random.choice(anomaly_types)
        anomaly = {"type": typ}
        # for same_invoice_diff_date, reuse same invoice num but change date
        if typ == "same_invoice_diff_date":
            # create a set of invoices that share number but different dates
            date_day = (idx % 28) + 1
            anomaly["date"] = f"2025-09-{date_day:02d}"
            data = make_invoice_data(idx, anomaly=anomaly, reuse_invoice_num=reused_invoice_num)
        else:
            data = make_invoice_data(idx, anomaly=anomaly)

        fname = f"invoice_{idx:02d}_{typ}.pdf"
        path = os.path.join(OUT_DIR, fname)
        draw_invoice_pdf(path, data)
        generated.append(path)

    print(f"Generated {len(generated)} PDFs in {OUT_DIR}")
    for p in generated:
        print(" -", p)


if __name__ == '__main__':
    generate_all()
#!/usr/bin/env python3
"""
Comprehensive PDF Report Generator for Invoice Processing

This module generates detailed, professional PDF reports containing:
- Invoice processing summary
- Detailed validation analysis with tables
- Duplication detection results
- AI reasoning and recommendations
- Database information and statistics
- Visual charts and graphs

Features:
- Professional formatting with corporate styling
- Detailed tables with validation results
- Visual indicators for pass/fail status
- Comprehensive AI analysis sections
- Executive summary for business stakeholders
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_pdf import PdfPages
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO
import base64

# PDF generation imports
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.platypus import Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white, red, green, blue, orange
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib import colors

@dataclass
class ReportData:
    """Data structure for PDF report generation"""
    # Processing results
    invoice_data: Dict[str, Any]
    validation_results: Dict[str, Any]
    duplication_analysis: Dict[str, Any]
    ai_reasoning: Dict[str, Any]
    document_classification: Dict[str, Any]
    database_ids: Dict[str, int]
    
    # Metadata
    processing_timestamp: str
    filename: str
    total_processing_time: Optional[float] = None
    errors: List[str] = None

class InvoicePDFReportGenerator:
    """Professional PDF report generator for invoice processing results"""
    
    def __init__(self, output_dir: str = "reports"):
        """Initialize the PDF report generator"""
        self.output_dir = output_dir
        self.ensure_output_directory()
        
        # Setup color scheme
        self.colors = {
            'primary': HexColor('#2E86AB'),      # Professional blue
            'secondary': HexColor('#A23B72'),     # Accent purple
            'success': HexColor('#2ECC71'),       # Green for success
            'light_green': HexColor('#D5EFDF'),   # Light green background
            'warning': HexColor('#F39C12'),       # Orange for warnings
            'danger': HexColor('#E74C3C'),        # Red for errors
            'light_gray': HexColor('#F8F9FA'),    # Light background
            'dark_gray': HexColor('#6C757D'),     # Text gray
            'white': white,
            'black': black
        }
        
        # Setup styles
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def _create_custom_styles(self):
        """Create custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.colors['primary'],
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.colors['primary'],
            borderWidth=2,
            borderColor=self.colors['primary'],
            borderPadding=5,
            spaceAfter=12
        ))
        
        # Subsection style
        self.styles.add(ParagraphStyle(
            name='SubSection',
            parent=self.styles['Heading3'],
            fontSize=14,
            textColor=self.colors['secondary'],
            spaceAfter=8
        ))
        
        # Success text style
        self.styles.add(ParagraphStyle(
            name='SuccessText',
            parent=self.styles['Normal'],
            textColor=self.colors['success'],
            fontSize=12
        ))
        
        # Warning text style
        self.styles.add(ParagraphStyle(
            name='WarningText',
            parent=self.styles['Normal'],
            textColor=self.colors['warning'],
            fontSize=12
        ))
        
        # Error text style
        self.styles.add(ParagraphStyle(
            name='ErrorText',
            parent=self.styles['Normal'],
            textColor=self.colors['danger'],
            fontSize=12
        ))
        
        # Code/monospace style
        self.styles.add(ParagraphStyle(
            name='CodeStyle',
            parent=self.styles['Normal'],
            fontName='Courier',
            fontSize=10,
            leftIndent=20,
            backgroundColor=self.colors['light_gray']
        ))
    
    def generate_report(self, report_data: ReportData) -> str:
        """Generate comprehensive PDF report"""
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        invoice_data = report_data.invoice_data or {}
        invoice_num = invoice_data.get('invoice_number', 'UNKNOWN')
        if invoice_num is None:
            invoice_num = 'UNKNOWN'
        invoice_num = str(invoice_num).replace('/', '_')
        filename = f"invoice_analysis_{invoice_num}_{timestamp}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        print(f"📄 Generating comprehensive PDF report: {filename}")
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Build report content
        story = []
        
        # 1. Title page
        story.extend(self._create_title_page(report_data))
        story.append(PageBreak())
        
        # 2. Executive summary
        story.extend(self._create_executive_summary(report_data))
        story.append(PageBreak())
        
        # 3. Invoice details
        story.extend(self._create_invoice_details_section(report_data))
        story.append(PageBreak())
        
        # 4. Arithmetic validation analysis
        story.extend(self._create_validation_analysis_section(report_data))
        story.append(PageBreak())
        
        # 5. Duplication detection analysis
        story.extend(self._create_duplication_analysis_section(report_data))
        story.append(PageBreak())
        
        # 6. AI reasoning and recommendations
        story.extend(self._create_ai_reasoning_section(report_data))
        story.append(PageBreak())
        
        # 7. Technical details and database information
        story.extend(self._create_technical_details_section(report_data))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ PDF report generated successfully: {filepath}")
        return filepath
    
    def _create_title_page(self, report_data: ReportData) -> List:
        """Create professional title page"""
        content = []
        
        # Main title
        content.append(Spacer(1, 2*inch))
        content.append(Paragraph(
            "COMPREHENSIVE INVOICE ANALYSIS REPORT",
            self.styles['CustomTitle']
        ))
        
        content.append(Spacer(1, 0.5*inch))
        
        # Invoice information
        # Safe confidence score extraction
        ai_confidence = 0.0
        if report_data.ai_reasoning and isinstance(report_data.ai_reasoning.get('confidence_score'), (int, float)):
            ai_confidence = report_data.ai_reasoning.get('confidence_score', 0)
        
        invoice_info = [
            ['Invoice Number:', report_data.invoice_data.get('invoice_number', 'N/A')],
            ['Supplier:', report_data.invoice_data.get('supplier_name', 'N/A')],
            ['Total Amount:', f"₹{report_data.invoice_data.get('total_amount', 0) or 0:,.2f}"],
            ['Processing Date:', report_data.processing_timestamp],
            ['Document Type:', (report_data.document_classification or {}).get('document_type', 'UNKNOWN')],
            ['AI Confidence:', self._safe_percentage_format(ai_confidence)]
        ]
        
        info_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.colors['light_gray']),
            ('TEXTCOLOR', (0, 0), (-1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        content.append(info_table)
        content.append(Spacer(1, 1*inch))
        
        # Status indicators
        val_status = "✅ VALID" if report_data.validation_results.get('overall_passed') else "❌ INVALID"
        dup_status = "🚨 DUPLICATE" if report_data.duplication_analysis.get('is_duplicate') else "✅ UNIQUE"
        
        status_data = [
            ['Validation Status:', val_status],
            ['Duplication Status:', dup_status],
            ['Tests Performed:', f"{(report_data.validation_results or {}).get('tests_run', 0)} validation tests"],
            ['Processing Status:', '✅ COMPLETED' if not report_data.errors else '⚠️ WITH WARNINGS']
        ]
        
        status_table = Table(status_data, colWidths=[2*inch, 3*inch])
        status_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (0, -1), white),
            ('TEXTCOLOR', (1, 0), (1, -1), black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        content.append(status_table)
        
        return content
    
    def _create_executive_summary(self, report_data: ReportData) -> List:
        """Create executive summary section"""
        content = []
        
        content.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        content.append(Spacer(1, 0.2*inch))
        
        # Overall assessment with safe confidence extraction
        ai_confidence = 0.0
        if report_data.ai_reasoning and isinstance(report_data.ai_reasoning.get('confidence_score'), (int, float)):
            ai_confidence = report_data.ai_reasoning.get('confidence_score', 0)
        
        # Safe access to validation and duplication results
        validation_results = report_data.validation_results or {}
        duplication_analysis = report_data.duplication_analysis or {}
        
        overall_status = "APPROVED" if (validation_results.get('overall_passed') and 
                                       not duplication_analysis.get('is_duplicate')) else "REQUIRES REVIEW"
        
        summary_text = f"""
        <b>Invoice Assessment:</b> {overall_status}<br/>
        <b>Processing Confidence:</b> {self._safe_percentage_format(ai_confidence)}<br/>
        <b>Recommendation:</b> {duplication_analysis.get('recommended_action', 'MANUAL_REVIEW')}
        """
        
        content.append(Paragraph(summary_text, self.styles['Normal']))
        content.append(Spacer(1, 0.2*inch))
        
        # Key findings
        content.append(Paragraph("Key Findings:", self.styles['SubSection']))
        
        findings = []
        
        # Validation findings with safe access
        if validation_results.get('overall_passed'):
            findings.append("• ✅ All arithmetic validations passed successfully")
        else:
            failed_tests = validation_results.get('tests_failed', 0)
            findings.append(f"• ❌ {failed_tests} validation test(s) failed")
        
        # Duplication findings with safe access
        if duplication_analysis.get('is_duplicate'):
            dup_confidence = self._safe_confidence_score(duplication_analysis.get('confidence_score'))
            findings.append(f"• 🚨 Potential duplicate detected ({self._safe_percentage_format(dup_confidence)} confidence)")
        else:
            findings.append("• ✅ No duplicates detected - invoice appears unique")
        
        # AI reasoning findings with safe access
        ai_reasoning = report_data.ai_reasoning or {}
        if ai_reasoning.get('recommendations'):
            findings.append(f"• 💡 {len(ai_reasoning['recommendations'])} AI recommendations provided")
        
        for finding in findings:
            content.append(Paragraph(finding, self.styles['Normal']))
        
        content.append(Spacer(1, 0.3*inch))
        
        # Business impact summary
        content.append(Paragraph("Business Impact:", self.styles['SubSection']))
        
        impact_text = ai_reasoning.get('business_impact', 'Business impact analysis not available.')
        if len(impact_text) > 500:
            impact_text = impact_text[:500] + "... [See AI Reasoning section for full analysis]"
        
        cleaned_impact_text = self._clean_markdown_text(impact_text)
        content.append(Paragraph(cleaned_impact_text, self.styles['Normal']))
        
        return content
    
    def _create_invoice_details_section(self, report_data: ReportData) -> List:
        """Create detailed invoice information section"""
        content = []
        
        content.append(Paragraph("INVOICE DETAILS", self.styles['SectionHeader']))
        content.append(Spacer(1, 0.2*inch))
        
        # Basic invoice information
        invoice_data = report_data.invoice_data
        
        basic_info = [
            ['Field', 'Value'],
            ['Invoice Number', invoice_data.get('invoice_number', 'N/A')],
            ['Invoice Date', invoice_data.get('invoice_date', 'N/A')],
            ['Supplier Name', invoice_data.get('supplier_name', 'N/A')],
            ['Supplier GSTIN', invoice_data.get('supplier_gstin', 'N/A')],
            ['Buyer Name', invoice_data.get('buyer_name', 'N/A')],
            ['Taxable Value', f"₹{invoice_data.get('taxable_value', 0) or 0:,.2f}"],
            ['Total Tax', f"₹{invoice_data.get('total_tax', 0) or 0:,.2f}"],
            ['Total Amount', f"₹{invoice_data.get('total_amount', 0) or 0:,.2f}"],
            ['Payment Terms', invoice_data.get('payment_terms', 'N/A')]
        ]
        
        basic_table = Table(basic_info, colWidths=[2*inch, 3.5*inch])
        basic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        content.append(basic_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Line items table
        content.append(Paragraph("Line Items Details:", self.styles['SubSection']))
        
        line_items = invoice_data.get('line_items', [])
        if line_items:
            line_item_data = [['Item', 'HSN Code', 'Qty', 'Unit Price', 'Taxable Value', 'GST Rate', 'GST Amount']]
            
            for i, item in enumerate(line_items, 1):
                line_item_data.append([
                    f"Item {i}: {item.get('description', 'N/A')[:20]}...",
                    item.get('hsn_code', 'N/A'),
                    f"{item.get('quantity', 0) or 0:.2f}",
                    f"₹{item.get('unit_price', 0) or 0:,.2f}",
                    f"₹{item.get('taxable_value', 0) or 0:,.2f}",
                    f"{item.get('gst_rate', 0) or 0:.1f}%",
                    f"₹{item.get('gst_amount', 0) or 0:,.2f}"
                ])
            
            line_items_table = Table(line_item_data, colWidths=[1.5*inch, 0.8*inch, 0.6*inch, 1*inch, 1*inch, 0.7*inch, 1*inch])
            line_items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['secondary']),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
            ]))
            
            content.append(line_items_table)
        else:
            content.append(Paragraph("No line items data available.", self.styles['Normal']))
        
        return content
    
    def _create_validation_analysis_section(self, report_data: ReportData) -> List:
        """Create comprehensive validation analysis section"""
        content = []
        
        content.append(Paragraph("ARITHMETIC VALIDATION ANALYSIS", self.styles['SectionHeader']))
        content.append(Spacer(1, 0.2*inch))
        
        val_result = report_data.validation_results
        
        # Validation summary with enhanced tax-related information
        summary_data = [
            ['Validation Metric', 'Result'],
            ['Total Tests Performed', str(val_result.get('tests_run', 0))],
            ['Tests Passed', str(val_result.get('tests_passed', 0))],
            ['Tests Failed', str(val_result.get('tests_failed', 0))],
        ]
        
        # Add tax-related failure info if available
        if val_result.get('tax_tests_failed', 0) > 0:
            summary_data.extend([
                ['Tax-related Failures (Ignored)', str(val_result.get('tax_tests_failed', 0))],
                ['Critical Non-tax Failures', str(val_result.get('non_tax_tests_failed', 0))]
            ])
        
        summary_data.extend([
            ['Suggestions Provided', str(val_result.get('suggestions_count', 0))],
            ['Overall Status', '✅ VALID' if val_result.get('overall_passed') else '❌ INVALID']
        ])
        
        if val_result.get('validation_notes', {}).get('tax_failures_ignored'):
            summary_data.append(['Note', 'Tax-related validation failures are ignored'])
        
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        content.append(summary_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Valid Checks Log section
        valid_checks = val_result.get('valid_checks_log', [])
        if valid_checks:
            content.append(Paragraph("✅ Valid Checks Log:", self.styles['SubSection']))
            content.append(Spacer(1, 0.1*inch))
            
            valid_checks_data = [['Test Name', 'Expected', 'Actual', 'Tolerance', 'Description']]
            
            for check in valid_checks[:8]:  # Limit to first 8 valid checks for space
                valid_checks_data.append([
                    check.get('test_name', 'N/A')[:30] + '...' if len(check.get('test_name', '')) > 30 else check.get('test_name', 'N/A'),
                    f"{check.get('expected', 0):.2f}",
                    f"{check.get('actual', 0):.2f}",
                    f"±{check.get('tolerance', 0):.2f}",
                    check.get('description', 'N/A')[:40] + '...' if len(check.get('description', '')) > 40 else check.get('description', 'N/A')
                ])
            
            if len(valid_checks) > 8:
                valid_checks_data.append([f"... and {len(valid_checks) - 8} more valid checks", '', '', '', ''])
            
            valid_checks_table = Table(valid_checks_data, colWidths=[1.8*inch, 0.8*inch, 0.8*inch, 0.6*inch, 1.8*inch])
            valid_checks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['success']),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_green']])
            ]))
            
            content.append(valid_checks_table)
            content.append(Spacer(1, 0.3*inch))
        
        # Detailed test results
        content.append(Paragraph("Detailed Validation Results:", self.styles['SubSection']))
        
        test_results = val_result.get('results', [])
        if test_results:
            # Filter only actual test results (not suggestions)
            actual_tests = [test for test in test_results if not test.get('is_suggestion', False)]
            
            if actual_tests:
                test_data = [['Test Name', 'Status', 'Expected', 'Actual', 'Error Message']]
                
                for test in actual_tests[:10]:  # Limit to first 10 tests for space
                    status = '✅ PASS' if test.get('passed') else '❌ FAIL'
                    expected = f"{test.get('expected', 0):.2f}" if test.get('expected') else 'N/A'
                    actual = f"{test.get('actual', 0):.2f}" if test.get('actual') else 'N/A'
                    error = test.get('error_message', '')[:50] + '...' if len(test.get('error_message', '')) > 50 else test.get('error_message', '')
                    
                    test_data.append([
                        test.get('test_name', 'Unknown Test'),
                        status,
                        expected,
                        actual,
                        error
                    ])
                
                test_table = Table(test_data, colWidths=[2*inch, 0.8*inch, 1*inch, 1*inch, 2.2*inch])
                test_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), self.colors['secondary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
                ]))
                
                content.append(test_table)
                
                if len(test_results) > 10:
                    content.append(Spacer(1, 0.1*inch))
                    content.append(Paragraph(f"... and {len(test_results) - 10} more test results", self.styles['Normal']))
        
        # AI validation reasoning
        content.append(Spacer(1, 0.3*inch))
        content.append(Paragraph("AI Validation Analysis:", self.styles['SubSection']))
        
        validation_reasoning = report_data.ai_reasoning.get('validation_reasoning', 'AI validation analysis not available.')
        if len(validation_reasoning) > 1000:
            validation_reasoning = validation_reasoning[:1000] + "... [Analysis truncated for space]"
        
        cleaned_validation_reasoning = self._clean_markdown_text(validation_reasoning)
        content.append(Paragraph(cleaned_validation_reasoning, self.styles['Normal']))
        
        return content
    
    def _create_duplication_analysis_section(self, report_data: ReportData) -> List:
        """Create duplication detection analysis section"""
        content = []
        
        content.append(Paragraph("DUPLICATION DETECTION ANALYSIS", self.styles['SectionHeader']))
        content.append(Spacer(1, 0.2*inch))
        
        dup_result = report_data.duplication_analysis
        
        # Duplication summary
        dup_confidence = self._safe_confidence_score(dup_result.get('confidence_score'))
        summary_data = [
            ['Analysis Metric', 'Result'],
            ['Duplication Status', '🚨 DUPLICATE DETECTED' if dup_result.get('is_duplicate') else '✅ UNIQUE INVOICE'],
            ['Confidence Score', self._safe_percentage_format(dup_confidence)],
            ['Recommended Action', dup_result.get('recommended_action', 'MANUAL_REVIEW')],
            ['Potential Matches Found', str(len(dup_result.get('duplicate_matches', [])))],
            ['Analysis Method', 'Enhanced AI-Powered Detection']
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2.5*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        content.append(summary_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Potential duplicate matches
        duplicate_matches = dup_result.get('duplicate_matches', [])
        if duplicate_matches:
            content.append(Paragraph("Potential Duplicate Matches:", self.styles['SubSection']))
            
            match_data = [['Original Invoice', 'Match Type', 'Confidence', 'Matching Fields', 'Recommendation']]
            
            for match in duplicate_matches[:5]:  # Limit to top 5 matches
                # Handle matching_fields as either dict or list
                matching_fields_data = match.get('matching_fields', {})
                if isinstance(matching_fields_data, dict):
                    # Convert dict to list of key-value pairs, limit to first 3
                    field_items = list(matching_fields_data.items())[:3]
                    matching_fields = ', '.join([f"{k}: {v}" for k, v in field_items])
                    if len(matching_fields_data) > 3:
                        matching_fields += f" (+{len(matching_fields_data) - 3} more)"
                elif isinstance(matching_fields_data, list):
                    # Handle as list (backward compatibility)
                    matching_fields = ', '.join(matching_fields_data[:3])
                    if len(matching_fields_data) > 3:
                        matching_fields += f" (+{len(matching_fields_data) - 3} more)"
                else:
                    # Fallback for other types
                    matching_fields = str(matching_fields_data) if matching_fields_data else 'N/A'
                
                match_confidence = self._safe_confidence_score(match.get('confidence_score'))
                match_data.append([
                    match.get('original_invoice_num', 'N/A'),
                    match.get('match_type', 'Unknown'),
                    self._safe_percentage_format(match_confidence),
                    matching_fields,
                    match.get('recommendation', 'Review Required')
                ])
            
            match_table = Table(match_data, colWidths=[1.2*inch, 1.2*inch, 0.8*inch, 1.5*inch, 1.3*inch])
            match_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.colors['danger']),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
            ]))
            
            content.append(match_table)
        else:
            content.append(Paragraph("✅ No potential duplicates found. Invoice appears to be unique.", self.styles['SuccessText']))
        
        # Analysis summary
        content.append(Spacer(1, 0.3*inch))
        content.append(Paragraph("Analysis Summary:", self.styles['SubSection']))
        
        analysis_summary = dup_result.get('analysis_summary', 'Duplication analysis summary not available.')
        content.append(Paragraph(analysis_summary, self.styles['Normal']))
        
        # AI duplication reasoning
        content.append(Spacer(1, 0.2*inch))
        content.append(Paragraph("AI Duplication Analysis:", self.styles['SubSection']))
        
        duplication_reasoning = report_data.ai_reasoning.get('duplication_reasoning', 'AI duplication analysis not available.')
        if len(duplication_reasoning) > 1000:
            duplication_reasoning = duplication_reasoning[:1000] + "... [Analysis truncated for space]"
        
        cleaned_duplication_reasoning = self._clean_markdown_text(duplication_reasoning)
        content.append(Paragraph(cleaned_duplication_reasoning, self.styles['Normal']))
        
        return content
    
    def _clean_markdown_text(self, text: str) -> str:
        """Remove markdown formatting from text for PDF display and ensure proper line breaks"""
        if not text:
            return text
        
        # Remove markdown headers (## and ###)
        text = re.sub(r'^#{1,6}\s*', '', text, flags=re.MULTILINE)
        
        # Remove bold formatting (**text** and __text__)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'__(.*?)__', r'\1', text)
        
        # Remove italic formatting (*text* and _text_)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'_(.*?)_', r'\1', text)
        
        # Remove code blocks (```text```)
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        
        # Remove inline code (`text`)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove links [text](url)
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove horizontal rules (--- or ***)
        text = re.sub(r'^[-*]{3,}\s*$', '', text, flags=re.MULTILINE)
        
        # Convert bullet points to proper format
        text = re.sub(r'^[-*+]\s+', '• ', text, flags=re.MULTILINE)
        
        # Ensure proper sentence spacing - add line breaks after periods when followed by uppercase
        text = re.sub(r'\.(\s+)([A-Z])', r'.<br/>\2', text)
        
        # Clean up multiple newlines but preserve intentional line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Convert remaining newlines to HTML line breaks for PDF
        text = re.sub(r'\n(?!\n)', '<br/>', text)
        text = re.sub(r'\n\n', '<br/><br/>', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _safe_confidence_score(self, value: Any) -> float:
        """Safely extract confidence score, handling None values"""
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, dict) and 'confidence_score' in value:
            return self._safe_confidence_score(value['confidence_score'])
        return 0.0
    
    def _safe_percentage_format(self, value: Any) -> str:
        """Safely format a value as percentage, handling None and invalid values"""
        try:
            safe_value = self._safe_confidence_score(value)
            return f"{safe_value:.1%}"
        except (TypeError, ValueError):
            return "0.0%"

    def _create_ai_reasoning_section(self, report_data: ReportData) -> List:
        """Create AI reasoning and recommendations section"""
        content = []
        
        content.append(Paragraph("AI REASONING & RECOMMENDATIONS", self.styles['SectionHeader']))
        content.append(Spacer(1, 0.2*inch))
        
        ai_reasoning = report_data.ai_reasoning
        
        # AI confidence and overview with safe extraction
        ai_reasoning = report_data.ai_reasoning or {}
        ai_confidence = 0.0
        if isinstance(ai_reasoning.get('confidence_score'), (int, float)):
            ai_confidence = ai_reasoning.get('confidence_score', 0)
        
        confidence_data = [
            ['AI Analysis Metric', 'Result'],
            ['Overall Confidence', self._safe_percentage_format(ai_confidence)],
            ['Analysis Type', 'Comprehensive Validation & Duplication'],
            ['Processing Status', 'Completed Successfully' if not ai_reasoning.get('fallback_mode') else 'Fallback Mode'],
            ['Recommendations Generated', str(len(ai_reasoning.get('recommendations', [])))]
        ]
        
        confidence_table = Table(confidence_data, colWidths=[3*inch, 2.5*inch])
        confidence_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['primary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        content.append(confidence_table)
        content.append(Spacer(1, 0.3*inch))
        
        # AI Recommendations
        content.append(Paragraph("AI-Generated Recommendations:", self.styles['SubSection']))
        
        recommendations = ai_reasoning.get('recommendations', [])
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                cleaned_rec = self._clean_markdown_text(str(rec))
                content.append(Paragraph(f"{i}. {cleaned_rec}", self.styles['Normal']))
                content.append(Spacer(1, 0.1*inch))
        else:
            content.append(Paragraph("No specific recommendations generated.", self.styles['Normal']))
        
        content.append(Spacer(1, 0.3*inch))
        
        # Business Impact Assessment
        content.append(Paragraph("Business Impact Assessment:", self.styles['SubSection']))
        
        business_impact = ai_reasoning.get('business_impact', 'Business impact assessment not available.')
        cleaned_business_impact = self._clean_markdown_text(business_impact)
        content.append(Paragraph(cleaned_business_impact, self.styles['Normal']))
        
        content.append(Spacer(1, 0.3*inch))
        
        # Final AI Explanation
        content.append(Paragraph("AI Final Analysis:", self.styles['SubSection']))
        
        final_explanation = ai_reasoning.get('final_explanation', 'Final AI explanation not available.')
        cleaned_final_explanation = self._clean_markdown_text(final_explanation)
        content.append(Paragraph(cleaned_final_explanation, self.styles['Normal']))
        
        return content
    
    def _create_technical_details_section(self, report_data: ReportData) -> List:
        """Create technical details and database information section"""
        content = []
        
        content.append(Paragraph("TECHNICAL DETAILS & DATABASE INFORMATION", self.styles['SectionHeader']))
        content.append(Spacer(1, 0.2*inch))
        
        # Document classification details
        content.append(Paragraph("Document Classification:", self.styles['SubSection']))
        
        # Document classification details with safe confidence extraction
        doc_class = report_data.document_classification
        class_confidence = self._safe_confidence_score(doc_class.get('confidence_score'))
        class_data = [
            ['Classification Attribute', 'Value'],
            ['Document Type', doc_class.get('document_type', 'UNKNOWN')],
            ['Classification Confidence', self._safe_percentage_format(class_confidence)],
            ['Keywords Detected', ', '.join(doc_class.get('detected_keywords', [])[:10])],
            ['Processing Method', 'AI-Powered Classification']
        ]
        
        class_table = Table(class_data, colWidths=[3*inch, 3*inch])
        class_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['secondary']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        content.append(class_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Database records
        content.append(Paragraph("Database Records Created:", self.styles['SubSection']))
        
        db_ids = report_data.database_ids
        db_data = [
            ['Record Type', 'Database ID'],
            ['Document Record', str(db_ids.get('doc_id', 'N/A'))],
            ['Invoice Record', str(db_ids.get('invoice_id', 'N/A'))],
            ['Supplier Company', str(db_ids.get('supplier_id', 'N/A'))],
            ['Buyer Company', str(db_ids.get('buyer_id', 'N/A')) if db_ids.get('buyer_id') else 'None']
        ]
        
        db_table = Table(db_data, colWidths=[3*inch, 2*inch])
        db_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.colors['dark_gray']),
            ('TEXTCOLOR', (0, 0), (-1, 0), white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, self.colors['light_gray']])
        ]))
        
        content.append(db_table)
        content.append(Spacer(1, 0.3*inch))
        
        # Processing metadata
        content.append(Paragraph("Processing Metadata:", self.styles['SubSection']))
        
        metadata = [
            f"• Processing Timestamp: {report_data.processing_timestamp}",
            f"• Source Filename: {report_data.filename}",
            f"• Processing Time: {report_data.total_processing_time:.2f}s" if report_data.total_processing_time else "• Processing Time: Not recorded",
            f"• Errors Encountered: {len(report_data.errors or [])}"
        ]
        
        for meta in metadata:
            content.append(Paragraph(meta, self.styles['Normal']))
        
        # Errors section if any
        if report_data.errors:
            content.append(Spacer(1, 0.2*inch))
            content.append(Paragraph("Processing Errors/Warnings:", self.styles['SubSection']))
            
            for error in report_data.errors:
                content.append(Paragraph(f"• {error}", self.styles['ErrorText']))
        
        # Footer
        content.append(Spacer(1, 0.5*inch))
        content.append(Paragraph(
            "This report was generated by the Intelligent Invoice Processing System. "
            "All analysis results are based on AI-powered validation and duplication detection algorithms.",
            self.styles['Normal']
        ))
        
        return content

def generate_comprehensive_report(processing_results: Dict[str, Any], output_dir: str = "reports") -> str:
    """
    Generate a comprehensive PDF report from processing results
    
    Args:
        processing_results: The results dictionary from dual_input_ai_agent processing
        output_dir: Directory to save the report
    
    Returns:
        str: Path to the generated PDF report
    """
    
    # Extract data from processing results
    extracted_data = processing_results.get('extracted_data')
    
    # Convert ExtractedInvoiceData to dict if needed
    if extracted_data and hasattr(extracted_data, '__dict__'):
        invoice_data = {
            'invoice_number': getattr(extracted_data, 'invoice_number', None),
            'supplier_name': getattr(extracted_data, 'supplier_name', None),
            'buyer_name': getattr(extracted_data, 'buyer_name', None),
            'invoice_date': getattr(extracted_data, 'invoice_date', None),
            'total_amount': getattr(extracted_data, 'total_amount', None),
            'taxable_value': getattr(extracted_data, 'taxable_value', None),
            'total_tax': getattr(extracted_data, 'total_tax', None),
            'supplier_gstin': getattr(extracted_data, 'supplier_gstin', None),
            'payment_terms': getattr(extracted_data, 'payment_terms', None),
            'line_items': getattr(extracted_data, 'line_items', [])
        }
    else:
        # Provide default structure if extracted_data is None
        invoice_data = {
            'invoice_number': 'Unknown',
            'supplier_name': 'Unknown',
            'buyer_name': 'Unknown',
            'invoice_date': 'Unknown',
            'total_amount': 0.0,
            'taxable_value': 0.0,
            'total_tax': 0.0,
            'supplier_gstin': 'Unknown',
            'payment_terms': 'Unknown',
            'line_items': []
        }
    
    # Create report data structure
    report_data = ReportData(
        invoice_data=invoice_data,
        validation_results=processing_results.get('validation_result', {}),
        duplication_analysis=processing_results.get('duplication_analysis', {}),
        ai_reasoning=processing_results.get('ai_reasoning', {}),
        document_classification=processing_results.get('document_classification', {}),
        database_ids=processing_results.get('database_ids', {}),
        processing_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        filename=getattr(extracted_data, 'filename', 'unknown.pdf') if extracted_data else 'unknown.pdf',
        errors=processing_results.get('errors', [])
    )
    
    # Generate report
    generator = InvoicePDFReportGenerator(output_dir)
    return generator.generate_report(report_data)

def main():
    """Main function for testing"""
    print("📄 PDF Report Generator initialized")
    print("Use generate_comprehensive_report() function to create reports from processing results")

if __name__ == "__main__":
    main()