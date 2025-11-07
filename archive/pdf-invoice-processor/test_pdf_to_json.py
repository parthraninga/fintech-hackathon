#!/usr/bin/env python3
"""
Test the PDF to JSON converter with sample text
"""

import json
from pdf_to_json import PDFToJSON

def test_text_to_json():
    """Test the text to JSON conversion without a PDF"""
    
    # Sample invoice text (simulating OCR output)
    sample_invoice_text = """
    INVOICE
    
    From:
    TechCorp Solutions Pvt Ltd
    123 Business Park, Sector 14
    Gurgaon, Haryana - 122001
    GSTIN: 06AABCT1234L1Z5
    Phone: +91-124-4567890
    Email: billing@techcorp.com
    
    To:
    MegaMart Enterprises
    456 Trade Center, Connaught Place
    New Delhi - 110001
    GSTIN: 07AABME5678P1W3
    
    Invoice Number: INV-2024-0156
    Date: 15/03/2024
    Due Date: 30/03/2024
    PO Number: PO-2024-789
    
    Description                     Qty    Rate      Amount
    Software License - Annual        1    75000     75000
    Implementation Services          1    25000     25000
    Training & Support              1    15000     15000
    
    Subtotal:                                     115000
    CGST @ 9%:                                     10350
    SGST @ 9%:                                     10350
    
    Total Amount:                                 135700
    
    Amount in Words: One Lakh Thirty Five Thousand Seven Hundred Rupees Only
    
    Terms & Conditions:
    1. Payment within 15 days
    2. Late payment charges: 2% per month
    3. Subject to Delhi jurisdiction
    """
    
    print("🧪 Testing Text to JSON Conversion")
    print("=" * 50)
    
    try:
        # Initialize converter
        converter = PDFToJSON()
        
        # Convert text to JSON
        json_result = converter.convert_to_json(sample_invoice_text)
        
        # Save result
        output_file = "test_invoice_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON saved to: {output_file}")
        
        # Display results
        print("\n📊 Extracted Data Summary:")
        print("-" * 30)
        
        if isinstance(json_result, dict) and "error" not in json_result:
            print(f"Invoice Number: {json_result.get('invoice_number', 'N/A')}")
            print(f"Date: {json_result.get('invoice_date', 'N/A')}")
            
            vendor = json_result.get('vendor', {})
            print(f"Vendor: {vendor.get('name', 'N/A')}")
            print(f"Vendor GSTIN: {vendor.get('gstin', 'N/A')}")
            
            customer = json_result.get('customer', {})
            print(f"Customer: {customer.get('name', 'N/A')}")
            
            totals = json_result.get('totals', {})
            print(f"Subtotal: ₹{totals.get('subtotal', 0):,.2f}")
            print(f"CGST: ₹{totals.get('cgst', 0):,.2f}")
            print(f"SGST: ₹{totals.get('sgst', 0):,.2f}")
            print(f"Grand Total: ₹{totals.get('grand_total', 0):,.2f}")
            
            items = json_result.get('items', [])
            print(f"\nItems ({len(items)}):")
            for i, item in enumerate(items, 1):
                desc = item.get('description', 'N/A')
                qty = item.get('quantity', 0)
                amount = item.get('total_amount', 0)
                print(f"  {i}. {desc} | Qty: {qty} | Amount: ₹{amount:,.2f}")
        
        else:
            print("❌ Error in conversion:")
            print(json.dumps(json_result, indent=2))
        
        print("\n💡 To process a real PDF file:")
        print("   python pdf_to_json.py your_invoice.pdf")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_to_json()