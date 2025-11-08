#!/usr/bin/env python3
"""
Sample Data Insertion Script for GST Extractor Dashboard Demo
Inserts sample companies, invoices, and product data for dashboard testing
"""

import sqlite3
import os
from datetime import datetime, timedelta
import json
import random

def insert_sample_data():
    """Insert comprehensive sample data for dashboard demonstration"""
    
    # Database path - try multiple possible locations
    possible_db_paths = [
        '/Users/admin/gst-extractor/invoice_management.db',
        '/Users/admin/gst-extractor/pdf-ocr-app/invoice_management.db',
        '/Users/admin/gst-extractor/invoices.db'
    ]
    
    db_path = None
    for path in possible_db_paths:
        if os.path.exists(path):
            db_path = path
            break
    
    if not db_path:
        print("❌ No database found. Creating new database...")
        db_path = '/Users/admin/gst-extractor/invoice_management.db'
    
    print(f"📂 Using database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🚀 Starting sample data insertion...")
        
        # Sample companies data with realistic Indian company information
        companies_data = [
            {
                'legal_name': 'Tata Consultancy Services Ltd',
                'gstin': '27AAACT2727Q1ZZ',
                'address': 'Nirmal Building, Nariman Point',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'phone': '+91-22-6778-9595',
                'email': 'info@tcs.com'
            },
            {
                'legal_name': 'Infosys Limited',
                'gstin': '29AAACI1681G1ZT',
                'address': 'Electronics City Phase 1',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'phone': '+91-80-2852-0261',
                'email': 'info@infosys.com'
            },
            {
                'legal_name': 'Reliance Industries Ltd',
                'gstin': '24AAACR5055K1Z5',
                'address': 'Maker Chambers IV, Nariman Point',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'phone': '+91-22-3555-5000',
                'email': 'info@ril.com'
            },
            {
                'legal_name': 'Wipro Limited',
                'gstin': '29AAACW3775F004',
                'address': 'Doddakannelli, Sarjapur Road',
                'city': 'Bangalore',
                'state': 'Karnataka',
                'phone': '+91-80-2844-0011',
                'email': 'info@wipro.com'
            },
            {
                'legal_name': 'HCL Technologies Ltd',
                'gstin': '06AAACH1781L1ZG',
                'address': 'Plot No 3A, Sector 126',
                'city': 'Noida',
                'state': 'Uttar Pradesh',
                'phone': '+91-120-254-6000',
                'email': 'info@hcl.com'
            }
        ]
        
        # Insert companies
        print("📊 Inserting companies...")
        for company in companies_data:
            cursor.execute("""
                INSERT OR REPLACE INTO companies 
                (legal_name, gstin, address, city, state, phone, email) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                company['legal_name'], company['gstin'], company['address'],
                company['city'], company['state'], company['phone'], company['email']
            ))
            
            company_id = cursor.lastrowid
            
            # Insert GST details
            cursor.execute("""
                INSERT OR REPLACE INTO gst_companies 
                (gstin, legal_name, trade_name, pan, status, state, api_source) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                company['gstin'], company['legal_name'], 
                company['legal_name'], company['gstin'][2:12], 
                'Active', company['state'], 'SAMPLE_DATA'
            ))
        
        # Sample products with HSN codes
        products_data = [
            {'canonical_name': 'Software Development Services', 'hsn_code': '998314', 'description': 'Custom software development', 'unit_of_measure': 'HOURS'},
            {'canonical_name': 'IT Consulting Services', 'hsn_code': '998313', 'description': 'Technology consulting', 'unit_of_measure': 'HOURS'},
            {'canonical_name': 'Cloud Infrastructure Services', 'hsn_code': '998311', 'description': 'Cloud hosting and management', 'unit_of_measure': 'MONTH'},
            {'canonical_name': 'Data Analytics Platform', 'hsn_code': '998312', 'description': 'Analytics software license', 'unit_of_measure': 'LICENSE'},
            {'canonical_name': 'Mobile App Development', 'hsn_code': '998314', 'description': 'Mobile application development', 'unit_of_measure': 'PROJECT'},
            {'canonical_name': 'Digital Marketing Services', 'hsn_code': '998399', 'description': 'Online marketing campaigns', 'unit_of_measure': 'CAMPAIGN'},
            {'canonical_name': 'Cybersecurity Solutions', 'hsn_code': '998313', 'description': 'Security consulting and tools', 'unit_of_measure': 'MONTH'},
            {'canonical_name': 'AI/ML Model Development', 'hsn_code': '998314', 'description': 'Machine learning solutions', 'unit_of_measure': 'MODEL'}
        ]
        
        print("🛍️ Inserting products...")
        for product in products_data:
            cursor.execute("""
                INSERT OR REPLACE INTO products 
                (canonical_name, hsn_code, description, unit_of_measure) 
                VALUES (?, ?, ?, ?)
            """, (product['canonical_name'], product['hsn_code'], product['description'], product['unit_of_measure']))
        
        # Generate sample invoices for the last 6 months
        print("📋 Generating sample invoices...")
        
        # Get company IDs
        cursor.execute("SELECT company_id FROM companies")
        company_ids = [row[0] for row in cursor.fetchall()]
        
        # Get product IDs
        cursor.execute("SELECT product_id FROM products")
        product_ids = [row[0] for row in cursor.fetchall()]
        
        # Generate invoices for each month
        base_date = datetime.now()
        invoice_statuses = ['Paid', 'Pending', 'Processed', 'Draft']
        
        for month_offset in range(6):
            month_date = base_date - timedelta(days=30 * month_offset)
            
            # Generate 3-8 invoices per month per company
            for company_id in company_ids:
                num_invoices = random.randint(2, 6)
                
                for inv_num in range(num_invoices):
                    invoice_date = month_date - timedelta(days=random.randint(0, 28))
                    invoice_number = f"INV-{invoice_date.strftime('%Y%m')}-{company_id:03d}-{inv_num+1:03d}"
                    
                    # Random invoice details
                    total_value = random.randint(50000, 500000)  # 50K to 5L
                    cgst_rate = random.choice([9, 14, 18])
                    sgst_rate = cgst_rate
                    igst_rate = 0 if random.choice([True, False]) else cgst_rate * 2
                    
                    cgst_amount = (total_value * cgst_rate / 100) if igst_rate == 0 else 0
                    sgst_amount = (total_value * sgst_rate / 100) if igst_rate == 0 else 0
                    igst_amount = (total_value * igst_rate / 100) if igst_rate > 0 else 0
                    
                    grand_total = total_value + cgst_amount + sgst_amount + igst_amount
                    
                    # Get a document ID for this invoice
                    cursor.execute("SELECT doc_id FROM documents ORDER BY RANDOM() LIMIT 1")
                    doc_result = cursor.fetchone()
                    doc_id = doc_result[0] if doc_result else 1
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO invoices 
                        (doc_id, invoice_num, supplier_company_id, invoice_date, 
                         taxable_value, total_tax, total_value, status, validation, duplication) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc_id, invoice_number, company_id, invoice_date.strftime('%Y-%m-%d'),
                        total_value, cgst_amount + sgst_amount + igst_amount, grand_total, 
                        random.choice(invoice_statuses), 1, 0
                    ))
                    
                    invoice_id = cursor.lastrowid
                    
                    # Add 1-4 invoice items per invoice
                    num_items = random.randint(1, 4)
                    for item_num in range(num_items):
                        product_id = random.choice(product_ids)
                        quantity = random.randint(1, 20)
                        rate = random.randint(5000, 50000)
                        amount = quantity * rate
                        
                        # Get product details for HSN code
                        cursor.execute("SELECT hsn_code FROM products WHERE product_id = ?", (product_id,))
                        hsn_result = cursor.fetchone()
                        hsn_code = hsn_result[0] if hsn_result else '998314'
                        
                        gst_rate = random.choice([5, 12, 18, 28])
                        gst_amount = amount * gst_rate / 100
                        total_amount = amount + gst_amount
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO invoice_item 
                            (invoice_id, product_id, hsn_code, item_description, quantity, 
                             unit_price, taxable_value, gst_rate, gst_amount, total_amount) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (invoice_id, product_id, hsn_code, f'Service Item {item_num+1}', 
                              quantity, rate, amount, gst_rate, gst_amount, total_amount))
        
        # Generate some payment records
        print("💳 Adding payment records...")
        cursor.execute("SELECT invoice_id, total_value FROM invoices WHERE status = 'Paid'")
        paid_invoices = cursor.fetchall()
        
        payment_methods = ['NEFT', 'RTGS', 'UPI', 'Cheque', 'Net Banking']
        
        for invoice_id, amount in paid_invoices[:20]:  # Add payments for first 20 paid invoices
            payment_date = base_date - timedelta(days=random.randint(1, 180))
            # Get document ID for the invoice
            cursor.execute("SELECT doc_id FROM invoices WHERE invoice_id = ?", (invoice_id,))
            doc_result = cursor.fetchone()
            doc_id = doc_result[0] if doc_result else 1
            
            cursor.execute("""
                INSERT OR REPLACE INTO payment 
                (doc_id, invoice_id, payment_date, amount, payment_method, status, transaction_ref) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, invoice_id, payment_date.strftime('%Y-%m-%d'), 
                amount, random.choice(payment_methods), 'COMPLETED',
                f'TXN{random.randint(1000000000, 9999999999)}'
            ))
        
        # Insert some documents
        print("📄 Adding document records...")
        sample_documents = [
            'invoice_001.pdf', 'invoice_002.pdf', 'tax_invoice_003.pdf',
            'commercial_invoice_004.pdf', 'service_invoice_005.pdf'
        ]
        
        for i, doc_name in enumerate(sample_documents):
            processing_date = base_date - timedelta(days=random.randint(1, 30))
            cursor.execute("""
                INSERT OR REPLACE INTO documents 
                (doc_type, filename, file_size_bytes, analysis_confidence, raw_data) 
                VALUES (?, ?, ?, ?, ?)
            """, (
                'INVOICE', doc_name, random.randint(100000, 1000000),
                random.randint(85, 98), '{"sample": "data"}'
            ))
        
        conn.commit()
        
        # Display summary
        print("\n✅ Sample data insertion completed!")
        print("\n📊 Database Summary:")
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        print(f"   Companies: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM gst_companies")
        print(f"   GST Records: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM products")
        print(f"   Products: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM invoices")
        print(f"   Invoices: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM invoice_item")
        print(f"   Invoice Items: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM payment")
        print(f"   Payments: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM documents")
        print(f"   Documents: {cursor.fetchone()[0]}")
        
        cursor.execute("SELECT SUM(total_value) FROM invoices")
        total_revenue = cursor.fetchone()[0] or 0
        print(f"   Total Revenue: ₹{total_revenue:,.2f}")
        
        print("\n🎯 Dashboard is now ready with sample data!")
        print("   Refresh the dashboard page to see the data visualization.")
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    insert_sample_data()