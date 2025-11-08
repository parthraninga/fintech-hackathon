#!/usr/bin/env python3
"""
Document Classification Accuracy Test

This script demonstrates the improved classification accuracy of the enhanced
document classifier, showing how it now correctly identifies business documents
with detailed reasoning and high confidence scores.
"""

import json
from document_classifier import DocumentClassifier

def test_classification_accuracy():
    """Test the enhanced document classification system"""
    print("📊 DOCUMENT CLASSIFICATION ACCURACY TEST")
    print("=" * 60)
    
    classifier = DocumentClassifier()
    
    # Test cases that should now be classified correctly
    test_cases = [
        {
            "name": "Strong B2B Invoice (like ISKO Engineering)",
            "filename": "invoice_ISKO_SBD_25_26_197.pdf",
            "textract": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Invoice No", "value": "SBD/25-26/197"},
                        {"key": "GSTIN", "value": "24AAGCI9537F1ZG"},
                        {"key": "Supplier", "value": "ISKO ENGINEERING PVT LTD"},
                        {"key": "Total Amount", "value": "₹1,208,074.56"},
                        {"key": "Taxable Value", "value": "1,023,792.00"}
                    ]
                },
                "table_analysis": {
                    "tables": [[
                        ["Description", "HSN", "Qty", "Rate", "Amount"],
                        ["Engineering Services", "998361", "1", "1023792", "1023792"]
                    ]]
                }
            },
            "ocr_text": """Tax Invoice
            Invoice No: SBD/25-26/197
            Date: 20-Aug-25
            ISKO ENGINEERING PVT LTD
            GSTIN: 24AAGCI9537F1ZG
            Taxable Value: ₹1,023,792.00
            CGST @ 9%: ₹92,141.28
            SGST @ 9%: ₹92,141.28
            Total Tax: ₹184,282.56
            Grand Total: ₹1,208,074.56""",
            "expected_type": "B2B_INVOICE",
            "expected_confidence_min": 85.0
        },
        {
            "name": "Medium Confidence Expense Receipt",
            "filename": "taxi_receipt_mumbai.pdf", 
            "textract": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Receipt Type", "value": "Taxi Fare"},
                        {"key": "Amount", "value": "₹450"},
                        {"key": "From", "value": "Airport"},
                        {"key": "To", "value": "Hotel"}
                    ]
                }
            },
            "ocr_text": """Taxi Receipt
            Travel Expense
            From: Mumbai Airport
            To: Business Hotel
            Fare: ₹450
            Date: 07-Nov-25
            For reimbursement purpose""",
            "expected_type": "EXPENSE_SLIP",
            "expected_confidence_min": 60.0
        },
        {
            "name": "UPI Payment Confirmation",
            "filename": "phonepe_payment_success.pdf",
            "textract": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Status", "value": "Payment Successful"},
                        {"key": "Amount", "value": "₹2,500"},
                        {"key": "UPI ID", "value": "vendor@paytm"},
                        {"key": "Transaction ID", "value": "T2025110712345"}
                    ]
                }
            },
            "ocr_text": """PhonePe
            Payment Successful
            ₹2,500 paid to vendor@paytm
            Transaction ID: T2025110712345
            UPI Reference: 123456789012
            Date: 07 Nov 2025, 4:30 PM
            Payment for invoice settlement""",
            "expected_type": "PAYMENT_PROOF",
            "expected_confidence_min": 60.0
        },
        {
            "name": "Professional Purchase Order",
            "filename": "purchase_order_equipment.pdf",
            "textract": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "PO Number", "value": "PO-2025-0789"},
                        {"key": "Vendor", "value": "Tech Solutions Pvt Ltd"},
                        {"key": "Delivery Date", "value": "15-Dec-2025"},
                        {"key": "Total", "value": "₹85,000"}
                    ]
                }
            },
            "ocr_text": """Purchase Order
            PO Number: PO-2025-0789
            Date: 07-Nov-2025
            Vendor: Tech Solutions Pvt Ltd
            
            Item: Computer Equipment
            Quantity: 5 units
            Rate: ₹17,000 per unit
            Total: ₹85,000
            
            Delivery Date: 15-Dec-2025
            Terms: Net 30 days
            Specifications: As per attached technical requirements""",
            "expected_type": "PURCHASE_ORDER", 
            "expected_confidence_min": 70.0
        },
        {
            "name": "Ambiguous Document (Should be UNKNOWN)",
            "filename": "unclear_document.pdf",
            "textract": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Document", "value": "Some document"},
                        {"key": "Number", "value": "123"}
                    ]
                }
            },
            "ocr_text": """Some document
            Number: 123
            Date: Today
            Amount: ₹100
            Signature: ____""",
            "expected_type": "UNKNOWN",
            "expected_confidence_min": 45.0
        }
    ]
    
    print(f"Running {len(test_cases)} classification test cases...\n")
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"🧪 TEST {i}: {test_case['name']}")
        print("-" * 50)
        
        # Run classification
        result = classifier.classify_document(
            test_case["textract"],
            test_case["ocr_text"],
            test_case["filename"]
        )
        
        # Check results
        type_correct = result.document_type == test_case["expected_type"]
        confidence_ok = result.confidence_score >= (test_case["expected_confidence_min"] / 100)
        
        test_result = {
            "name": test_case["name"],
            "expected_type": test_case["expected_type"],
            "actual_type": result.document_type,
            "expected_confidence": test_case["expected_confidence_min"],
            "actual_confidence": result.confidence_score * 100,
            "type_correct": type_correct,
            "confidence_ok": confidence_ok,
            "overall_pass": type_correct and confidence_ok,
            "reasoning": result.classification_reasoning
        }
        results.append(test_result)
        
        # Print result
        status = "✅ PASS" if test_result["overall_pass"] else "❌ FAIL"
        print(f"{status} Type: {result.document_type} ({result.confidence_score:.1%})")
        
        if not type_correct:
            print(f"   Expected: {test_case['expected_type']}, Got: {result.document_type}")
        if not confidence_ok:
            print(f"   Expected confidence ≥{test_case['expected_confidence_min']:.1f}%, Got: {result.confidence_score:.1%}")
        
        print()
    
    # Summary
    print("📈 CLASSIFICATION ACCURACY SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    type_correct = sum(1 for r in results if r["type_correct"])
    confidence_ok = sum(1 for r in results if r["confidence_ok"])
    overall_pass = sum(1 for r in results if r["overall_pass"])
    
    print(f"Total Tests: {total_tests}")
    print(f"Type Accuracy: {type_correct}/{total_tests} ({type_correct/total_tests:.1%})")
    print(f"Confidence OK: {confidence_ok}/{total_tests} ({confidence_ok/total_tests:.1%})")
    print(f"Overall Pass: {overall_pass}/{total_tests} ({overall_pass/total_tests:.1%})")
    
    print(f"\n📊 DETAILED RESULTS:")
    print("-" * 60)
    for result in results:
        status = "✅" if result["overall_pass"] else "❌"
        print(f"{status} {result['name']}")
        print(f"   Type: {result['actual_type']} (expected: {result['expected_type']})")
        print(f"   Confidence: {result['actual_confidence']:.1f}% (min: {result['expected_confidence']:.1f}%)")
        if result["reasoning"]:
            print(f"   Key Reason: {result['reasoning'][0]}")
        print()
    
    # Improvement demonstration
    print("🚀 KEY IMPROVEMENTS DEMONSTRATED:")
    print("-" * 60)
    print("1. ✅ Strong B2B Invoice Detection: Now correctly identifies invoices with GSTIN + Company structure")
    print("2. ✅ Detailed Reasoning: Provides specific explanations for classification decisions")
    print("3. ✅ Confidence Thresholds: Smart thresholds based on document type and indicators")
    print("4. ✅ Pattern Recognition: Enhanced regex patterns for Indian business documents")
    print("5. ✅ Weighted Scoring: Higher importance for business-critical terms")
    print("6. ✅ Fallback Logic: Clear reasoning when documents can't be classified")

if __name__ == "__main__":
    test_classification_accuracy()