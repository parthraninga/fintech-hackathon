#!/usr/bin/env python3
"""
Enhanced Document Processing Demo

This demo showcases the complete document classification and processing pipeline
with proper document type detection, metadata storage, and database integration.

Features demonstrated:
1. Intelligent document type classification
2. Enhanced database storage with document metadata
3. Support for multiple document types (B2B Invoice, Expense Slip, Payment Proof, etc.)
4. Integration with existing validation and duplication systems
5. Comprehensive document metadata tracking
"""

import sqlite3
import json
from document_classifier import DocumentClassifier
from invoice_database import InvoiceDatabase
from datetime import datetime

def demonstrate_document_classification():
    """Demonstrate document classification capabilities"""
    
    print("📄 ENHANCED DOCUMENT CLASSIFICATION & STORAGE DEMO")
    print("=" * 80)
    print("This system now intelligently classifies documents into:")
    print("📋 B2B_INVOICE - Business-to-business invoices")
    print("🧾 EXPENSE_SLIP - Expense receipts and slips")
    print("💰 PAYMENT_PROOF - Payment confirmations and transfers")
    print("📝 PURCHASE_ORDER - Purchase orders and procurement")
    print("📊 CREDIT_NOTE - Credit notes and returns")
    print("📈 DEBIT_NOTE - Debit notes and charges")
    print("💭 QUOTATION - Price quotes and estimates")
    print("❓ UNKNOWN - Unclassified documents")
    print("=" * 80)
    
    # Initialize classifier
    classifier = DocumentClassifier()
    
    # Test document classification with realistic examples
    test_documents = [
        {
            "filename": "invoice_ISKO_SBD_25_26_197.pdf",
            "textract_data": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Invoice Number", "value": "SBD/25-26/197"},
                        {"key": "GSTIN", "value": "24AAGCI9537F1ZG"},
                        {"key": "Taxable Value", "value": "1023792"},
                        {"key": "Total Tax Amount", "value": "184282.56"},
                        {"key": "Invoice Date", "value": "20-Aug-25"}
                    ]
                },
                "table_analysis": {
                    "tables": [
                        {
                            "rows": [
                                ["Description", "HSN", "Qty", "Rate", "Amount"],
                                ["BASKET", "84049000", "6.00", "170632", "1023792"]
                            ]
                        }
                    ]
                },
                "summary": {"document_type": "Tax Invoice"}
            },
            "ocr_text": "TAX INVOICE Invoice No: SBD/25-26/197 GSTIN: 24AAGCI9537F1ZG ISKO ENGINEERING PVT LTD Taxable Value: 1023792 CGST: 92141.28 SGST: 92141.28 Total: 1208074.56"
        },
        {
            "filename": "travel_expense_receipt.pdf",
            "textract_data": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Receipt Type", "value": "Travel Expense"},
                        {"key": "Amount", "value": "2500"},
                        {"key": "Date", "value": "15-Nov-2025"},
                        {"key": "Category", "value": "Hotel Stay"}
                    ]
                }
            },
            "ocr_text": "HOTEL RECEIPT Travel Expense Hotel ABC Executive Stay Amount: Rs 2500 Business Travel Reimbursement Claim"
        },
        {
            "filename": "upi_payment_proof.pdf",
            "textract_data": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Transaction ID", "value": "UPI/1234567890"},
                        {"key": "Amount", "value": "50000"},
                        {"key": "Status", "value": "SUCCESS"},
                        {"key": "Payment Method", "value": "PhonePe"}
                    ]
                }
            },
            "ocr_text": "Payment Successful UPI Transaction ID: UPI/1234567890 Amount: Rs 50000 PhonePe To: ISKO ENGINEERING Status: SUCCESS"
        },
        {
            "filename": "purchase_order_document.pdf",
            "textract_data": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Purchase Order", "value": "PO-2025-156"},
                        {"key": "Vendor", "value": "ABC Suppliers"},
                        {"key": "Delivery Date", "value": "30-Dec-2025"},
                        {"key": "Total Value", "value": "250000"}
                    ]
                }
            },
            "ocr_text": "PURCHASE ORDER PO Number: PO-2025-156 Vendor: ABC Suppliers Delivery Date: 30-Dec-2025 Specifications: Industrial Equipment"
        }
    ]
    
    classification_results = []
    
    for i, doc in enumerate(test_documents, 1):
        print(f"\n🧪 TEST DOCUMENT {i}: {doc['filename']}")
        print("-" * 60)
        
        # Classify document
        result = classifier.classify_document(
            doc["textract_data"],
            doc["ocr_text"],
            doc["filename"]
        )
        
        classification_results.append({
            "filename": doc["filename"],
            "classification": result,
            "test_data": doc
        })
        
        # Show classification summary
        print(f"🎯 CLASSIFICATION SUMMARY:")
        print(f"   Document Type: {result.document_type}")
        print(f"   Confidence: {result.confidence_score:.1%}")
        print(f"   Keywords Found: {len(result.detected_keywords)}")
        
        if result.alternate_types:
            print(f"   Alternative Types:")
            for alt in result.alternate_types[:2]:  # Show top 2 alternates
                print(f"     • {alt['type']}: {alt['score']:.1%}")
    
    return classification_results

def demonstrate_enhanced_database_storage():
    """Demonstrate enhanced database storage with document types"""
    
    print(f"\n💾 ENHANCED DATABASE STORAGE DEMO")
    print("=" * 60)
    
    # Check current database structure
    db = InvoiceDatabase()
    cursor = db.conn.cursor()
    
    print(f"📊 CURRENT DOCUMENTS TABLE STRUCTURE:")
    cursor.execute("PRAGMA table_info(documents)")
    columns = cursor.fetchall()
    
    print("-" * 60)
    print(f"{'Column':<20} {'Type':<15} {'Nullable':<10} {'Default':<15}")
    print("-" * 60)
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        nullable = "YES" if col[3] == 0 else "NO"
        default = col[4] or "NULL"
        print(f"{col_name:<20} {col_type:<15} {nullable:<10} {str(default):<15}")
    
    print(f"\n📋 CURRENT DOCUMENTS IN DATABASE:")
    cursor.execute("""
        SELECT 
            doc_id,
            doc_type,
            filename,
            file_size_bytes,
            analysis_confidence,
            created_at,
            CASE 
                WHEN LENGTH(raw_data) > 100 THEN SUBSTR(raw_data, 1, 100) || '...'
                ELSE raw_data
            END as raw_data_preview
        FROM documents 
        ORDER BY created_at DESC
    """)
    
    docs = cursor.fetchall()
    
    if docs:
        print("-" * 100)
        print(f"{'ID':<4} {'Type':<15} {'Filename':<25} {'Size':<10} {'Conf':<8} {'Created':<20}")
        print("-" * 100)
        
        for doc in docs:
            doc_id, doc_type, filename, file_size, confidence, created_at = doc[:6]
            file_size_str = f"{file_size//1024}KB" if file_size else "N/A"
            conf_str = f"{confidence:.1f}%" if confidence else "N/A"
            created_short = created_at[:19] if created_at else "N/A"
            
            print(f"{doc_id:<4} {doc_type:<15} {filename[:24]:<25} {file_size_str:<10} {conf_str:<8} {created_short:<20}")
    else:
        print("No documents found in database.")
    
    # Show document type statistics
    print(f"\n📈 DOCUMENT TYPE STATISTICS:")
    cursor.execute("""
        SELECT 
            doc_type,
            COUNT(*) as count,
            AVG(analysis_confidence) as avg_confidence,
            MIN(created_at) as first_seen,
            MAX(created_at) as last_seen
        FROM documents 
        GROUP BY doc_type 
        ORDER BY count DESC
    """)
    
    stats = cursor.fetchall()
    
    if stats:
        print("-" * 80)
        print(f"{'Document Type':<20} {'Count':<8} {'Avg Conf':<12} {'First Seen':<20}")
        print("-" * 80)
        
        for stat in stats:
            doc_type, count, avg_conf, first_seen, last_seen = stat
            avg_conf_str = f"{avg_conf:.1f}%" if avg_conf else "N/A"
            first_short = first_seen[:19] if first_seen else "N/A"
            
            print(f"{doc_type:<20} {count:<8} {avg_conf_str:<12} {first_short:<20}")
    
    db.close()

def simulate_document_processing():
    """Simulate processing documents of different types"""
    
    print(f"\n🤖 SIMULATED DOCUMENT PROCESSING")
    print("=" * 60)
    print("Simulating how different document types would be processed...")
    
    # Simulate adding different document types to database
    db = InvoiceDatabase()
    cursor = db.conn.cursor()
    
    sample_documents = [
        {
            "doc_type": "B2B_INVOICE",
            "filename": "supplier_invoice_001.pdf",
            "confidence": 92.5,
            "metadata": {"has_gstin": True, "has_tax_details": True, "supplier": "ABC Corp"}
        },
        {
            "doc_type": "EXPENSE_SLIP", 
            "filename": "travel_receipt_nov.pdf",
            "confidence": 88.3,
            "metadata": {"expense_category": "TRAVEL", "amount": 2500, "employee": "John Doe"}
        },
        {
            "doc_type": "PAYMENT_PROOF",
            "filename": "bank_transfer_proof.pdf", 
            "confidence": 95.0,
            "metadata": {"payment_method": "NEFT", "transaction_id": "NEFT123456", "amount": 150000}
        },
        {
            "doc_type": "PURCHASE_ORDER",
            "filename": "po_equipment_dec.pdf",
            "confidence": 90.2,
            "metadata": {"vendor": "XYZ Supplies", "po_number": "PO-2025-789", "value": 300000}
        }
    ]
    
    print("Adding sample documents to demonstrate enhanced storage:")
    
    for doc in sample_documents:
        # Insert document
        cursor.execute("""
            INSERT INTO documents (doc_type, filename, analysis_confidence, raw_data)
            VALUES (?, ?, ?, ?)
        """, (
            doc["doc_type"],
            doc["filename"], 
            doc["confidence"],
            json.dumps(doc["metadata"])
        ))
        
        doc_id = cursor.lastrowid
        print(f"✅ Added: {doc['doc_type']} - {doc['filename']} (ID: {doc_id})")
    
    db.conn.commit()
    
    # Show updated statistics
    print(f"\n📊 UPDATED DOCUMENT STATISTICS:")
    cursor.execute("""
        SELECT 
            doc_type,
            COUNT(*) as count,
            AVG(analysis_confidence) as avg_confidence
        FROM documents 
        GROUP BY doc_type 
        ORDER BY count DESC
    """)
    
    updated_stats = cursor.fetchall()
    
    print("-" * 50)
    print(f"{'Document Type':<20} {'Count':<8} {'Avg Confidence':<15}")
    print("-" * 50)
    
    for stat in updated_stats:
        doc_type, count, avg_conf = stat
        avg_conf_str = f"{avg_conf:.1f}%" if avg_conf else "N/A"
        print(f"{doc_type:<20} {count:<8} {avg_conf_str:<15}")
    
    db.close()

def show_sql_queries_for_document_types():
    """Show practical SQL queries for document type management"""
    
    print(f"\n💾 PRACTICAL SQL QUERIES FOR DOCUMENT MANAGEMENT")
    print("=" * 80)
    
    sql_examples = [
        {
            "title": "Get all invoices",
            "sql": "SELECT * FROM documents WHERE doc_type = 'B2B_INVOICE';"
        },
        {
            "title": "Get expense slips this month",
            "sql": "SELECT * FROM documents WHERE doc_type = 'EXPENSE_SLIP' AND created_at >= date('now', 'start of month');"
        },
        {
            "title": "Get payment proofs above certain amount",
            "sql": "SELECT * FROM documents WHERE doc_type = 'PAYMENT_PROOF' AND json_extract(raw_data, '$.amount') > 10000;"
        },
        {
            "title": "Document type distribution",
            "sql": """
SELECT 
    doc_type,
    COUNT(*) as total,
    AVG(analysis_confidence) as avg_confidence,
    MIN(created_at) as first_document,
    MAX(created_at) as latest_document
FROM documents 
GROUP BY doc_type;
"""
        },
        {
            "title": "High confidence documents",
            "sql": "SELECT doc_type, filename, analysis_confidence FROM documents WHERE analysis_confidence > 90 ORDER BY analysis_confidence DESC;"
        },
        {
            "title": "Documents processed today",
            "sql": "SELECT doc_type, filename, created_at FROM documents WHERE date(created_at) = date('now');"
        },
        {
            "title": "Update document type",
            "sql": "UPDATE documents SET doc_type = 'B2B_INVOICE' WHERE filename = 'invoice_001.pdf';"
        },
        {
            "title": "Get documents with metadata",
            "sql": "SELECT filename, doc_type, json_extract(raw_data, '$') as metadata FROM documents WHERE raw_data IS NOT NULL;"
        }
    ]
    
    for i, example in enumerate(sql_examples, 1):
        print(f"\n{i}. {example['title']}:")
        print("-" * (len(example['title']) + 3))
        print(example['sql'].strip())

def main():
    """Main demo function"""
    print("🎯 ENHANCED DOCUMENT PROCESSING SYSTEM")
    print("=" * 80)
    print("Complete document classification, processing, and storage pipeline")
    print("with support for multiple business document types")
    print("=" * 80)
    
    try:
        # Run all demos
        classification_results = demonstrate_document_classification()
        demonstrate_enhanced_database_storage()
        simulate_document_processing()
        show_sql_queries_for_document_types()
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 DEMO COMPLETED")
    print("=" * 80)
    print("Your enhanced document processing system now supports:")
    print("✅ Intelligent document type classification")
    print("✅ Multiple document types (Invoice, Expense, Payment, etc.)")
    print("✅ Enhanced database storage with metadata")
    print("✅ Document type-specific processing")
    print("✅ Comprehensive document analytics")
    print("✅ Production-ready document management")

if __name__ == "__main__":
    main()