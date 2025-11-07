#!/usr/bin/env python3
"""
Invoice Management Database

This script creates a comprehensive database for managing invoices, companies, 
products, and payments with proper relational structure and foreign key constraints.

Tables:
1. documents - Document metadata
2. companies - Company information with GST details
3. products - Product catalog with HSN codes
4. invoices - Invoice headers
5. invoice_item - Invoice line items
6. payment - Payment records
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import os

class InvoiceDatabase:
    def __init__(self, db_path: str = "invoice_management.db"):
        """Initialize the invoice database"""
        self.db_path = db_path
        self.conn = None
        self.init_database()
    
    def init_database(self):
        """Initialize database connection and create tables"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
        self.create_tables()
        print(f"✅ Invoice database initialized: {self.db_path}")
    
    def create_tables(self):
        """Create all required tables with proper relationships"""
        cursor = self.conn.cursor()
        
        # Table 1: documents
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filename VARCHAR(255),
                file_size_bytes INTEGER,
                analysis_confidence DECIMAL(5,2),
                raw_data TEXT  -- Store original Textract JSON
            )
        """)
        
        # Table 2: companies
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                company_id INTEGER PRIMARY KEY AUTOINCREMENT,
                legal_name VARCHAR(255) NOT NULL,
                gstin VARCHAR(15) UNIQUE,
                city VARCHAR(100),
                state VARCHAR(50),
                address TEXT,
                phone VARCHAR(20),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 3: products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                canonical_name VARCHAR(255) NOT NULL,
                hsn_code VARCHAR(10) NOT NULL,
                default_tax_rate DECIMAL(5,2) DEFAULT 18.00,
                description TEXT,
                unit_of_measure VARCHAR(20) DEFAULT 'NOS',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 4: invoices
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                invoice_num VARCHAR(50) NOT NULL,
                invoice_date DATE,
                supplier_company_id INTEGER,
                buyer_company_id INTEGER,
                taxable_value DECIMAL(15,2),
                total_tax DECIMAL(15,2),
                total_value DECIMAL(15,2),
                currency VARCHAR(3) DEFAULT 'INR',
                status VARCHAR(20) DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id),
                FOREIGN KEY (supplier_company_id) REFERENCES companies(company_id),
                FOREIGN KEY (buyer_company_id) REFERENCES companies(company_id)
            )
        """)
        
        # Table 5: invoice_item (corrected column name from invice_id to invoice_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_item (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_id INTEGER,
                hsn_code VARCHAR(10),
                item_description VARCHAR(255),
                quantity DECIMAL(10,2),
                unit_price DECIMAL(10,2),
                taxable_value DECIMAL(15,2),
                gst_rate DECIMAL(5,2),
                gst_amount DECIMAL(15,2),
                sgst_rate DECIMAL(5,2),
                sgst_amount DECIMAL(15,2),
                igst_rate DECIMAL(5,2),
                igst_amount DECIMAL(15,2),
                cgst_rate DECIMAL(5,2),
                cgst_amount DECIMAL(15,2),
                total_amount DECIMAL(15,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        """)
        
        # Table 6: payment (corrected column name from invice_id to invoice_id)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER,
                invoice_id INTEGER,
                payment_date DATE,
                payment_method VARCHAR(50),
                amount DECIMAL(15,2),
                transaction_ref VARCHAR(100),
                bank_details VARCHAR(255),
                status VARCHAR(20) DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id),
                FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(doc_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_companies_gstin ON companies(gstin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_hsn ON products(hsn_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_num ON invoices(invoice_num)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_item(invoice_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_invoice ON payment(invoice_id)")
        
        self.conn.commit()
        print("✅ All tables created successfully")
    
    def insert_sample_data(self):
        """Insert sample data for testing"""
        cursor = self.conn.cursor()
        
        # Sample documents
        cursor.execute("""
            INSERT OR IGNORE INTO documents (doc_type, filename, file_size_bytes, analysis_confidence)
            VALUES 
                ('INVOICE', '1.pdf', 909844, 89.03),
                ('RECEIPT', 'receipt_001.pdf', 245678, 95.50)
        """)
        
        # Sample companies
        cursor.execute("""
            INSERT OR IGNORE INTO companies (legal_name, gstin, city, state, address, phone)
            VALUES 
                ('ABC Electronics Pvt Ltd', '27ABCDE1234F1Z5', 'Mumbai', 'Maharashtra', 
                 '123 Business Park, Andheri East, Mumbai - 400069', '+91-9876543210'),
                ('XYZ Trading Co', '06XYZAB5678C1D9', 'Delhi', 'Delhi', 
                 '456 Trade Center, Connaught Place, New Delhi - 110001', '+91-9876543211'),
                ('PQR Manufacturing Ltd', '29PQRST9012E3F4', 'Bangalore', 'Karnataka', 
                 '789 Industrial Area, Whitefield, Bangalore - 560066', '+91-9876543212')
        """)
        
        # Sample products
        cursor.execute("""
            INSERT OR IGNORE INTO products (canonical_name, hsn_code, default_tax_rate, description, unit_of_measure)
            VALUES 
                ('LED TV 43 Inch', '8528', 18.00, '43 inch Smart LED Television', 'NOS'),
                ('Mobile Phone', '8517', 12.00, 'Smartphone with 128GB storage', 'NOS'),
                ('Laptop Computer', '8471', 18.00, 'Business laptop with 8GB RAM', 'NOS'),
                ('Cotton Fabric', '5208', 5.00, 'Cotton fabric per meter', 'MTR'),
                ('Steel Pipes', '7306', 18.00, 'Galvanized steel pipes', 'MTR')
        """)
        
        # Sample invoices
        cursor.execute("""
            INSERT OR IGNORE INTO invoices 
            (doc_id, invoice_num, invoice_date, supplier_company_id, buyer_company_id, 
             taxable_value, total_tax, total_value, status)
            VALUES 
                (1, 'INV-2024-001', '2024-11-01', 1, 2, 100000.00, 18000.00, 118000.00, 'PAID'),
                (2, 'INV-2024-002', '2024-11-05', 2, 3, 50000.00, 6000.00, 56000.00, 'PENDING')
        """)
        
        # Sample invoice items
        cursor.execute("""
            INSERT OR IGNORE INTO invoice_item 
            (invoice_id, product_id, hsn_code, item_description, quantity, unit_price, 
             taxable_value, gst_rate, gst_amount, sgst_rate, sgst_amount, cgst_rate, cgst_amount, total_amount)
            VALUES 
                (1, 1, '8528', 'LED TV 43 Inch Smart', 2.00, 50000.00, 100000.00, 
                 18.00, 18000.00, 9.00, 9000.00, 9.00, 9000.00, 118000.00),
                (2, 2, '8517', 'Mobile Phone Premium', 5.00, 10000.00, 50000.00, 
                 12.00, 6000.00, 6.00, 3000.00, 6.00, 3000.00, 56000.00)
        """)
        
        # Sample payments
        cursor.execute("""
            INSERT OR IGNORE INTO payment 
            (doc_id, invoice_id, payment_date, payment_method, amount, transaction_ref, status)
            VALUES 
                (1, 1, '2024-11-02', 'BANK_TRANSFER', 118000.00, 'TXN123456789', 'COMPLETED'),
                (2, 2, '2024-11-06', 'UPI', 56000.00, 'UPI987654321', 'PENDING')
        """)
        
        self.conn.commit()
        print("✅ Sample data inserted successfully")
    
    def get_table_info(self):
        """Display information about all tables"""
        cursor = self.conn.cursor()
        
        tables = ['documents', 'companies', 'products', 'invoices', 'invoice_item', 'payment']
        
        print("\n" + "="*80)
        print("📊 INVOICE DATABASE SCHEMA")
        print("="*80)
        
        for table in tables:
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            print(f"\n📋 Table: {table.upper()} ({count} rows)")
            print("-" * 40)
            for col in columns:
                col_name = col[1]
                col_type = col[2]
                is_pk = "PK" if col[5] else ""
                not_null = "NOT NULL" if col[3] else "NULLABLE"
                print(f"  {col_name:20} {col_type:15} {not_null:10} {is_pk}")
    
    def show_sample_data(self, limit: int = 3):
        """Show sample data from all tables"""
        cursor = self.conn.cursor()
        
        tables = ['documents', 'companies', 'products', 'invoices', 'invoice_item', 'payment']
        
        print("\n" + "="*80)
        print("📊 SAMPLE DATA")
        print("="*80)
        
        for table in tables:
            cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
            rows = cursor.fetchall()
            
            if rows:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                print(f"\n📋 {table.upper()}:")
                print("-" * 60)
                
                # Print header
                header = " | ".join([col[:12] for col in columns])
                print(header)
                print("-" * len(header))
                
                # Print data
                for row in rows:
                    row_str = " | ".join([str(val)[:12] if val is not None else "NULL" for val in row])
                    print(row_str)
    
    def get_invoice_summary(self):
        """Get comprehensive invoice summary with joins"""
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            i.invoice_num,
            i.invoice_date,
            s.legal_name as supplier,
            b.legal_name as buyer,
            i.taxable_value,
            i.total_tax,
            i.total_value,
            i.status,
            COUNT(ii.item_id) as item_count
        FROM invoices i
        LEFT JOIN companies s ON i.supplier_company_id = s.company_id
        LEFT JOIN companies b ON i.buyer_company_id = b.company_id
        LEFT JOIN invoice_item ii ON i.invoice_id = ii.invoice_id
        GROUP BY i.invoice_id
        ORDER BY i.invoice_date DESC
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        print("\n" + "="*100)
        print("📊 INVOICE SUMMARY")
        print("="*100)
        
        if results:
            print(f"{'Invoice#':<15} {'Date':<12} {'Supplier':<20} {'Buyer':<20} {'Taxable':<12} {'Tax':<10} {'Total':<12} {'Items':<6} {'Status'}")
            print("-" * 100)
            
            for row in results:
                print(f"{row[0]:<15} {row[1]:<12} {(row[2] or 'N/A')[:19]:<20} {(row[3] or 'N/A')[:19]:<20} "
                      f"{row[4] or 0:<12.2f} {row[5] or 0:<10.2f} {row[6] or 0:<12.2f} {row[8]:<6} {row[7]}")
        else:
            print("No invoices found.")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("📝 Database connection closed")

def main():
    """Main function to create and initialize the database"""
    print("🚀 Creating Invoice Management Database...")
    
    # Initialize database
    db = InvoiceDatabase()
    
    # Insert sample data
    db.insert_sample_data()
    
    # Display table information
    db.get_table_info()
    
    # Show sample data
    db.show_sample_data()
    
    # Show invoice summary
    db.get_invoice_summary()
    
    # Keep connection open for further operations
    print(f"\n✅ Database ready for use: {db.db_path}")
    print("💡 Use the InvoiceDatabase class to interact with the database")
    
    return db

if __name__ == "__main__":
    database = main()
    
    # Example usage
    print("\n" + "="*80)
    print("📝 EXAMPLE USAGE:")
    print("="*80)
    print("""
# Connect to database
db = InvoiceDatabase('invoice_management.db')

# Insert new document
cursor = db.conn.cursor()
cursor.execute('''
    INSERT INTO documents (doc_type, filename) 
    VALUES (?, ?)
''', ('INVOICE', 'new_invoice.pdf'))

# Query invoices
cursor.execute('SELECT * FROM invoices WHERE status = ?', ('PENDING',))
pending_invoices = cursor.fetchall()

# Close connection
db.close()
    """)