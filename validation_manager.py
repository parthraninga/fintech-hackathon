#!/usr/bin/env python3
"""
Invoice Validation and Duplication Manager

This script demonstrates how to manage validation and duplication flags for invoices.
"""

import sys
from invoice_database import InvoiceDatabase

def main():
    # Initialize database
    db = InvoiceDatabase("invoice_management.db")
    
    print("📋 INVOICE VALIDATION & DUPLICATION MANAGER")
    print("=" * 60)
    
    # Show current status
    print("\n1. Current Invoice Status:")
    status = db.get_invoice_status(1)
    if status:
        print(f"   Invoice: {status['invoice_num']}")
        print(f"   Validated: {'✅ Yes' if status['is_validated'] else '❌ No'}")
        print(f"   Duplicate: {'⚠️  Yes' if status['is_duplicate'] else '✅ No'}")
        print(f"   Status: {status['status']}")
        print(f"   Total: ₹{status['total_value']:,.2f}")
    
    # Validate the invoice
    print(f"\n2. Validating Invoice 1...")
    db.validate_invoice(1, is_valid=True)
    
    # Check for duplicates (this will return False since it's the only one)
    print(f"\n3. Checking for Duplicates...")
    is_dup = db.check_for_duplicates("SBD/25-26/197", 1, 1208074.56)
    if is_dup:
        print("   ⚠️  Potential duplicate found!")
        db.mark_as_duplicate(1, is_duplicate=True)
    else:
        print("   ✅ No duplicates found")
    
    # Show updated status
    print(f"\n4. Updated Invoice Status:")
    updated_status = db.get_invoice_status(1)
    if updated_status:
        print(f"   Invoice: {updated_status['invoice_num']}")
        print(f"   Validated: {'✅ Yes' if updated_status['is_validated'] else '❌ No'}")
        print(f"   Duplicate: {'⚠️  Yes' if updated_status['is_duplicate'] else '✅ No'}")
        print(f"   Status: {updated_status['status']}")
    
    # Show validation summary
    print(f"\n5. Validation Summary:")
    summary = db.get_validation_summary()
    print(f"   Total Invoices: {summary['total_invoices']}")
    print(f"   Validated: {summary['validated_invoices']}")
    print(f"   Duplicates: {summary['duplicate_invoices']}")
    print(f"   Pending Validation: {summary['pending_validation']}")
    
    print("\n" + "=" * 60)
    print("✅ Validation and duplication management complete!")
    
    # Show SQL queries for manual management
    print(f"\n💡 Useful SQL Queries:")
    print(f"""
-- Check validation status
SELECT invoice_num, validation, duplication, status 
FROM invoices;

-- Mark invoice as validated
UPDATE invoices SET validation = 1 WHERE invoice_id = 1;

-- Mark invoice as duplicate
UPDATE invoices SET duplication = 1 WHERE invoice_id = 1;

-- Get all unvalidated invoices
SELECT * FROM invoices WHERE validation = 0;

-- Get all duplicate invoices
SELECT * FROM invoices WHERE duplication = 1;
""")
    
    db.close()

if __name__ == "__main__":
    main()