#!/usr/bin/env python3
"""
Test script for the PDF Invoice Extractor

This script demonstrates the usage of the InvoiceExtractor class
and tests its functionality without requiring an actual PDF file.
"""

import os
import sys
from invoice_extractor import InvoiceExtractor
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def create_sample_pdf_info():
    """
    Create sample extracted OCR text to test the AI processing part
    """
    sample_ocr_text = """
    TAX INVOICE
    
    Vendor Details:
    ABC Technology Solutions Pvt Ltd
    123 Tech Park, Sector 5
    Bangalore, Karnataka - 560001
    GSTIN: 29AABCT1234M1Z5
    Phone: +91-80-12345678
    
    Bill To:
    XYZ Corporation
    456 Business Plaza
    Mumbai, Maharashtra - 400001
    GSTIN: 27AAXYZ9876N1W2
    
    Invoice No: INV-2024-001
    Date: 15/03/2024
    Due Date: 30/03/2024
    
    Description                    Qty    Rate    Amount
    Web Development Services        1     50000   50000
    Mobile App Development          1     30000   30000
    Database Setup & Config         1     15000   15000
    
    Subtotal:                              95000
    CGST @ 9%:                             8550
    SGST @ 9%:                             8550
    Total Amount:                          112100
    
    Amount in Words: One Lakh Twelve Thousand One Hundred Rupees Only
    
    Terms & Conditions:
    Payment within 15 days
    Late payment charges applicable
    """
    
    return sample_ocr_text

def test_invoice_extractor():
    """
    Test the invoice extractor functionality
    """
    print("🧪 Testing PDF Invoice Extractor")
    print("=" * 50)
    
    try:
        # Initialize the extractor
        # Note: You'll need to set your Google API key in environment
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            print("⚠️  Warning: GOOGLE_API_KEY not set in environment")
            print("   Set it using: export GOOGLE_API_KEY='your_api_key_here'")
            print("   For now, we'll test OCR extraction only")
            extractor = InvoiceExtractor(google_api_key=None)
        else:
            extractor = InvoiceExtractor(google_api_key=api_key)
        
        # Test with sample OCR text (simulating extracted PDF content)
        print("📝 Testing AI processing with sample OCR text...")
        sample_text = create_sample_pdf_info()
        
        if api_key:
            # Test AI processing
            structured_data = extractor._structure_invoice_with_gemini(sample_text)
            
            if structured_data:
                # Save the structured data
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"invoice_structured_test_{timestamp}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(structured_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Successfully processed sample invoice data!")
                print(f"📄 Structured data saved to: {output_file}")
                print("\n📋 Extracted Invoice Summary:")
                print("-" * 30)
                print(f"Vendor: {structured_data.get('vendor', {}).get('name', 'N/A')}")
                print(f"Customer: {structured_data.get('customer', {}).get('name', 'N/A')}")
                print(f"Invoice No: {structured_data.get('invoice_number', 'N/A')}")
                print(f"Date: {structured_data.get('invoice_date', 'N/A')}")
                print(f"Items Count: {len(structured_data.get('items', []))}")
                print(f"Total Amount: ₹{structured_data.get('totals', {}).get('grand_total', 0):,.2f}")
                
                # Show items
                print("\n🛒 Items:")
                for i, item in enumerate(structured_data.get('items', []), 1):
                    print(f"  {i}. {item.get('description', 'N/A')} - ₹{item.get('total_amount', 0):,.2f}")
            else:
                print("❌ AI processing returned no data")
        else:
            print("⏭️  Skipping AI processing (no API key)")
        
        print("\n💡 To test with actual PDF files:")
        print("   invoice_extractor = InvoiceExtractor(google_api_key='your_key')")
        print("   result = invoice_extractor.extract_invoice('path/to/invoice.pdf')")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed:")
        print("pip install PyMuPDF opencv-python pytesseract langchain-google-genai pydantic")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_invoice_extractor()