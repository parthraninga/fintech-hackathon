#!/usr/bin/env python3
"""
Dashboard Service - Database Query Service for Financial Dashboard

This service provides aggregated data for the financial dashboard including:
- Key metrics (documents, companies, revenue, validation rates)
- Recent invoices
- Top companies by volume
- Revenue trends over time
- GST compliance statistics
"""

import sys
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from invoice_database import InvoiceDatabase

class DashboardService:
    """Service for dashboard data aggregation"""
    
    def __init__(self, db_path: str = "invoice_management.db"):
        self.db = InvoiceDatabase(db_path)
        
    def get_key_metrics(self) -> Dict[str, Any]:
        """Get key dashboard metrics"""
        cursor = self.db.conn.cursor()
        
        # Total documents
        cursor.execute("SELECT COUNT(*) FROM documents")
        total_documents = cursor.fetchone()[0]
        
        # Active companies (with GSTIN)
        cursor.execute("SELECT COUNT(*) FROM companies WHERE gstin IS NOT NULL")
        active_companies = cursor.fetchone()[0]
        
        # Total revenue (paid invoices)
        cursor.execute("SELECT COALESCE(SUM(total_value), 0) FROM invoices WHERE status = 'PAID'")
        total_revenue = float(cursor.fetchone()[0])
        
        # Recent invoices (last 30 days)
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        cursor.execute("SELECT COUNT(*) FROM invoices WHERE created_at >= ?", (thirty_days_ago,))
        recent_invoices = cursor.fetchone()[0]
        
        # Validation success rate
        cursor.execute("SELECT COUNT(*) FROM invoices")
        total_invoices = cursor.fetchone()[0]
        if total_invoices > 0:
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE validation = 1")
            validated_invoices = cursor.fetchone()[0]
            validation_rate = round((validated_invoices / total_invoices) * 100, 1)
        else:
            validation_rate = 0.0
        
        return {
            "totalDocuments": total_documents,
            "activeCompanies": active_companies,
            "totalRevenue": total_revenue,
            "recentInvoices": recent_invoices,
            "validationRate": validation_rate
        }
    
    def get_recent_invoices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent invoices with supplier information"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT 
                i.invoice_id,
                i.invoice_num,
                i.invoice_date,
                i.total_value,
                i.status,
                c.legal_name as supplier_name
            FROM invoices i
            LEFT JOIN companies c ON i.supplier_company_id = c.company_id
            ORDER BY i.created_at DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        invoices = []
        for row in results:
            invoice = dict(zip(columns, row))
            # Convert None values to appropriate defaults
            invoice['supplier_name'] = invoice['supplier_name'] or 'Unknown Supplier'
            invoice['invoice_date'] = invoice['invoice_date'] or datetime.now().strftime('%Y-%m-%d')
            invoice['total_value'] = float(invoice['total_value'] or 0)
            invoices.append(invoice)
        
        return invoices
    
    def get_top_companies(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top companies by invoice volume"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.company_id,
                c.legal_name,
                c.gstin,
                c.city,
                COUNT(i.invoice_id) as total_invoices,
                COALESCE(SUM(i.total_value), 0) as total_revenue
            FROM companies c
            LEFT JOIN invoices i ON c.company_id = i.supplier_company_id
            GROUP BY c.company_id, c.legal_name, c.gstin, c.city
            HAVING COUNT(i.invoice_id) > 0
            ORDER BY total_invoices DESC, total_revenue DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        companies = []
        for row in results:
            company = dict(zip(columns, row))
            company['total_revenue'] = float(company['total_revenue'] or 0)
            company['city'] = company['city'] or 'Unknown'
            companies.append(company)
        
        return companies
    
    def get_revenue_trends(self, months: int = 12) -> List[Dict[str, Any]]:
        """Get revenue trends by month"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', invoice_date) as month,
                COALESCE(SUM(total_value), 0) as revenue,
                COALESCE(SUM(total_tax), 0) as tax_amount,
                COUNT(*) as invoice_count
            FROM invoices
            WHERE invoice_date IS NOT NULL
                AND invoice_date >= date('now', '-{} months')
            GROUP BY strftime('%Y-%m', invoice_date)
            ORDER BY month DESC
            LIMIT ?
        """.format(months), (months,))
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        trends = []
        for row in results:
            trend = dict(zip(columns, row))
            trend['revenue'] = float(trend['revenue'] or 0)
            trend['tax_amount'] = float(trend['tax_amount'] or 0)
            trends.append(trend)
        
        return trends
    
    def get_compliance_data(self) -> Dict[str, Any]:
        """Get GST compliance statistics"""
        cursor = self.db.conn.cursor()
        
        # Total companies
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        
        # Companies with GSTIN
        cursor.execute("SELECT COUNT(*) FROM companies WHERE gstin IS NOT NULL AND gstin != ''")
        with_gstin = cursor.fetchone()[0]
        
        # Validation success rate
        cursor.execute("SELECT COUNT(*) FROM invoices")
        total_invoices = cursor.fetchone()[0]
        if total_invoices > 0:
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE validation = 1")
            validated = cursor.fetchone()[0]
            validation_success = round((validated / total_invoices) * 100, 1)
        else:
            validation_success = 0.0
        
        # Duplicate detection rate
        if total_invoices > 0:
            cursor.execute("SELECT COUNT(*) FROM invoices WHERE duplication = 1")
            duplicates = cursor.fetchone()[0]
            duplicate_detection = round((duplicates / total_invoices) * 100, 1)
        else:
            duplicate_detection = 0.0
        
        return {
            "total_companies": total_companies,
            "with_gstin": with_gstin,
            "validation_success": validation_success,
            "duplicate_detection": duplicate_detection
        }
    
    def get_product_analytics(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get product analytics by HSN code"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT 
                p.hsn_code,
                p.canonical_name,
                p.default_tax_rate,
                COUNT(ii.item_id) as usage_count,
                COALESCE(SUM(ii.total_amount), 0) as total_value
            FROM products p
            LEFT JOIN invoice_item ii ON p.product_id = ii.product_id
            GROUP BY p.product_id, p.hsn_code, p.canonical_name, p.default_tax_rate
            HAVING COUNT(ii.item_id) > 0
            ORDER BY usage_count DESC, total_value DESC
            LIMIT ?
        """, (limit,))
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        products = []
        for row in results:
            product = dict(zip(columns, row))
            product['total_value'] = float(product['total_value'] or 0)
            product['default_tax_rate'] = float(product['default_tax_rate'] or 0)
            products.append(product)
        
        return products
    
    def get_geographic_distribution(self) -> List[Dict[str, Any]]:
        """Get invoice distribution by state"""
        cursor = self.db.conn.cursor()
        
        cursor.execute("""
            SELECT 
                c.state,
                COUNT(i.invoice_id) as invoice_count,
                COALESCE(SUM(i.total_value), 0) as total_revenue,
                COUNT(DISTINCT c.company_id) as company_count
            FROM companies c
            LEFT JOIN invoices i ON c.company_id = i.supplier_company_id
            WHERE c.state IS NOT NULL AND c.state != ''
            GROUP BY c.state
            HAVING COUNT(i.invoice_id) > 0
            ORDER BY total_revenue DESC, invoice_count DESC
        """)
        
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        distribution = []
        for row in results:
            state_data = dict(zip(columns, row))
            state_data['total_revenue'] = float(state_data['total_revenue'] or 0)
            distribution.append(state_data)
        
        return distribution

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Usage: python3 dashboard_service.py <command>")
        print("Commands: metrics, recent_invoices, top_companies, revenue_trends, compliance, products, geography")
        return
    
    command = sys.argv[1]
    service = DashboardService()
    
    try:
        if command == 'metrics':
            data = service.get_key_metrics()
        elif command == 'recent_invoices':
            data = service.get_recent_invoices()
        elif command == 'top_companies':
            data = service.get_top_companies()
        elif command == 'revenue_trends':
            data = service.get_revenue_trends()
        elif command == 'compliance':
            data = service.get_compliance_data()
        elif command == 'products':
            data = service.get_product_analytics()
        elif command == 'geography':
            data = service.get_geographic_distribution()
        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
            return
        
        print(json.dumps(data, indent=2, default=str))
        
    except Exception as e:
        print(json.dumps({"error": f"Dashboard service error: {str(e)}"}, indent=2))

if __name__ == "__main__":
    main()