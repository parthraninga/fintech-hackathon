#!/usr/bin/env python3
"""
Comprehensive Arithmetic Validation Demo

This script demonstrates the complete arithmetic validation workflow:
1. Discovery of applicable arithmetic tests for invoice data
2. Execution of all possible validation tests
3. Detailed reporting of validation results
4. Integration with AI agent for automatic validation
5. Database updates based on validation results

Features:
- Auto-discovery of available tests based on data structure
- Comprehensive test execution with detailed results
- Integration with dual-input AI processing
- Validation reporting and database flag management
"""

import json
import os
from arithmetic_validator import ArithmeticValidator
from dual_input_ai_agent import DualInputInvoiceAI
from invoice_database import InvoiceDatabase

def demonstrate_arithmetic_validation():
    """Demonstrate the comprehensive arithmetic validation system"""
    
    print("🧮 ARITHMETIC VALIDATION SYSTEM DEMO")
    print("=" * 80)
    print("This demo shows how the system automatically:")
    print("1. 🔍 Discovers all possible arithmetic tests from invoice data")
    print("2. 🧪 Executes comprehensive validation tests")
    print("3. 📊 Reports detailed validation results")
    print("4. 🤖 Integrates with AI agent for automatic validation")
    print("5. 💾 Updates database validation flags")
    print("=" * 80)
    
    # Initialize validator
    validator = ArithmeticValidator()
    
    # Show available test types
    print("\n🧪 AVAILABLE ARITHMETIC TEST TYPES:")
    print("-" * 50)
    for i, test in enumerate(validator.available_tests, 1):
        print(f"{i:2d}. {test.name}")
        print(f"    Description: {test.description}")
        print(f"    Required Fields: {', '.join(test.required_fields)}")
        print(f"    Tolerance: ±{test.tolerance}")
        print()
    
    # Get current invoices
    db = InvoiceDatabase()
    cursor = db.conn.cursor()
    cursor.execute("SELECT invoice_id, invoice_num FROM invoices ORDER BY invoice_id")
    invoices = cursor.fetchall()
    
    print(f"📋 CURRENT INVOICES IN DATABASE: {len(invoices)}")
    print("-" * 50)
    for invoice in invoices:
        print(f"Invoice ID {invoice[0]}: {invoice[1]}")
    
    if not invoices:
        print("⚠️  No invoices found in database. Please process an invoice first.")
        return
    
    print(f"\n🔍 DETAILED VALIDATION ANALYSIS:")
    print("=" * 80)
    
    # Analyze each invoice
    for invoice_id, invoice_num in invoices:
        print(f"\n📄 ANALYZING INVOICE: {invoice_num} (ID: {invoice_id})")
        print("-" * 60)
        
        # Show current validation status
        status = db.get_invoice_status(invoice_id)
        if status:
            validation_status = "✅ VALIDATED" if status['is_validated'] else "❌ NOT VALIDATED"
            duplicate_status = "⚠️  DUPLICATE" if status['is_duplicate'] else "✅ UNIQUE"
            print(f"Current Status: {validation_status}, {duplicate_status}")
            print(f"Total Value: ₹{status['total_value']:,.2f}")
            print()
        
        # Discover applicable tests
        applicable_tests = validator.discover_applicable_tests(invoice_id)
        
        # Run full validation
        validation_result = validator.validate_invoice(invoice_id)
        
        # Show comprehensive results
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"   Tests Discovered: {len(applicable_tests)}/{len(validator.available_tests)}")
        print(f"   Tests Executed: {validation_result['tests_run']}")
        print(f"   Tests Passed: {validation_result['tests_passed']}")
        print(f"   Tests Failed: {validation_result['tests_failed']}")
        print(f"   Overall Result: {'✅ VALID' if validation_result['overall_passed'] else '❌ INVALID'}")
        
        # Show failed tests details
        if validation_result['tests_failed'] > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in validation_result['results']:
                if not result['passed']:
                    print(f"   • {result['test_name']}")
                    print(f"     Expected: {result['expected']:.2f}")
                    print(f"     Actual: {result['actual']:.2f}")
                    print(f"     Error: {result['error_message']}")
    
    # Show overall database validation statistics
    print(f"\n📈 OVERALL VALIDATION STATISTICS:")
    print("=" * 50)
    stats = db.get_validation_summary()
    print(f"Total Invoices: {stats['total_invoices']}")
    print(f"Validated Invoices: {stats['validated_invoices']}")
    print(f"Duplicate Invoices: {stats['duplicate_invoices']}")
    print(f"Pending Validation: {stats['pending_validation']}")
    success_rate = (stats['validated_invoices'] / stats['total_invoices'] * 100) if stats['total_invoices'] > 0 else 0
    print(f"Validation Success Rate: {success_rate:.1f}%")
    
    # Close connections
    validator.close()
    db.close()
    
    print(f"\n✅ Arithmetic validation demo completed!")
    print("=" * 80)

def demonstrate_ai_integration():
    """Demonstrate AI agent integration with arithmetic validation"""
    
    print("\n🤖 AI AGENT INTEGRATION WITH ARITHMETIC VALIDATION")
    print("=" * 80)
    print("This shows how arithmetic validation is automatically integrated")
    print("into the AI agent processing pipeline.")
    print("=" * 80)
    
    # Check for required input files
    textract_file = "textract_analysis.json"
    ocr_file = "1_ocr.json"
    
    if not os.path.exists(textract_file) or not os.path.exists(ocr_file):
        print(f"⚠️  Required input files not found:")
        print(f"   Textract JSON: {textract_file} {'✅' if os.path.exists(textract_file) else '❌'}")
        print(f"   OCR JSON: {ocr_file} {'✅' if os.path.exists(ocr_file) else '❌'}")
        print("\n💡 To test AI integration, you need to:")
        print("   1. Run textract_analyzer.py on a PDF to create textract_analysis.json")
        print("   2. Run tesseract_ocr.py on a PDF to create OCR JSON")
        print("   3. Then run this demo again")
        return
    
    print("📁 Input files found:")
    print(f"   Textract JSON: {textract_file} ✅")
    print(f"   OCR JSON: {ocr_file} ✅")
    
    print(f"\n🚀 Processing invoice with AI agent (includes automatic validation)...")
    
    try:
        # Initialize AI agent
        ai_agent = DualInputInvoiceAI()
        
        # Process with dual inputs (this now includes automatic arithmetic validation)
        result = ai_agent.process_dual_inputs(textract_file, ocr_file)
        
        # Show results
        print(f"\n📊 AI PROCESSING RESULTS:")
        print("-" * 50)
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print(f"Processing Step: {result.get('processing_step', 'Unknown')}")
            print(f"Errors: {len(result.get('errors', []))}")
            
            # Show validation results if available
            if 'validation_result' in result and result['validation_result']:
                val_result = result['validation_result']
                print(f"\n🧮 AUTOMATIC ARITHMETIC VALIDATION:")
                print(f"   Tests Run: {val_result['tests_run']}")
                print(f"   Passed: {val_result['tests_passed']}")
                print(f"   Failed: {val_result['tests_failed']}")
                print(f"   Overall: {'✅ VALID' if val_result['overall_passed'] else '❌ INVALID'}")
                
                # Show database ID
                if 'database_ids' in result and 'invoice_id' in result['database_ids']:
                    print(f"   Invoice ID: {result['database_ids']['invoice_id']}")
            
            # Show AI messages
            if 'messages' in result:
                print(f"\n💬 AI AGENT MESSAGES:")
                for msg in result['messages']:
                    if hasattr(msg, 'content'):
                        print(f"   {msg.content}")
        
        ai_agent.close()
        
    except Exception as e:
        print(f"❌ AI processing error: {e}")
        import traceback
        traceback.print_exc()

def show_validation_sql_examples():
    """Show practical SQL examples for validation management"""
    
    print("\n💾 PRACTICAL SQL EXAMPLES FOR VALIDATION MANAGEMENT")
    print("=" * 80)
    
    sql_examples = [
        {
            "title": "Get all unvalidated invoices",
            "sql": "SELECT invoice_id, invoice_num, total_value, validation, duplication FROM invoices WHERE validation = 0;"
        },
        {
            "title": "Get all validated invoices",
            "sql": "SELECT invoice_id, invoice_num, total_value, validation, duplication FROM invoices WHERE validation = 1;"
        },
        {
            "title": "Get all duplicate invoices",
            "sql": "SELECT invoice_id, invoice_num, total_value, validation, duplication FROM invoices WHERE duplication = 1;"
        },
        {
            "title": "Get validation statistics",
            "sql": """
SELECT 
    COUNT(*) as total_invoices,
    SUM(CASE WHEN validation = 1 THEN 1 ELSE 0 END) as validated_count,
    SUM(CASE WHEN duplication = 1 THEN 1 ELSE 0 END) as duplicate_count,
    ROUND(AVG(CASE WHEN validation = 1 THEN 1.0 ELSE 0.0 END) * 100, 2) as validation_rate
FROM invoices;
"""
        },
        {
            "title": "Mark specific invoice as validated",
            "sql": "UPDATE invoices SET validation = 1 WHERE invoice_num = 'SBD/25-26/197';"
        },
        {
            "title": "Mark specific invoice as duplicate",
            "sql": "UPDATE invoices SET duplication = 1 WHERE invoice_num = 'SBD/25-26/197';"
        },
        {
            "title": "Reset validation status",
            "sql": "UPDATE invoices SET validation = 0, duplication = 0 WHERE invoice_id = 1;"
        },
        {
            "title": "Get invoices with validation details",
            "sql": """
SELECT 
    i.invoice_num,
    i.invoice_date,
    i.total_value,
    CASE WHEN i.validation = 1 THEN '✅ Validated' ELSE '❌ Not Validated' END as validation_status,
    CASE WHEN i.duplication = 1 THEN '⚠️ Duplicate' ELSE '✅ Unique' END as duplicate_status,
    c.legal_name as supplier
FROM invoices i
LEFT JOIN companies c ON i.supplier_company_id = c.company_id
ORDER BY i.invoice_date DESC;
"""
        }
    ]
    
    for i, example in enumerate(sql_examples, 1):
        print(f"\n{i}. {example['title']}:")
        print("-" * (len(example['title']) + 3))
        print(example['sql'].strip())

def main():
    """Main demo function"""
    print("🎯 COMPREHENSIVE ARITHMETIC VALIDATION SYSTEM")
    print("=" * 80)
    print("This system automatically discovers and executes arithmetic tests")
    print("to validate invoice data integrity and mathematical accuracy.")
    print("=" * 80)
    
    try:
        # Run basic arithmetic validation demo
        demonstrate_arithmetic_validation()
        
        # Show AI integration
        demonstrate_ai_integration()
        
        # Show SQL examples
        show_validation_sql_examples()
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 DEMO COMPLETED")
    print("=" * 80)
    print("Your arithmetic validation system is ready for production use!")
    print("Key features:")
    print("✅ Auto-discovery of applicable arithmetic tests")
    print("✅ Comprehensive validation execution")
    print("✅ Detailed reporting and error analysis")
    print("✅ Integration with AI agent pipeline")
    print("✅ Database validation flag management")
    print("✅ SQL utilities for validation workflow")

if __name__ == "__main__":
    main()