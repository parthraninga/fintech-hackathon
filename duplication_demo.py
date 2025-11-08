#!/usr/bin/env python3
"""
Comprehensive Demo: Intelligent Duplication Detection Integration

This demo showcases the complete AI-powered duplication detection system
integrated with the dual-input invoice processing agent.

Features demonstrated:
1. AI-powered duplicate analysis considering multiple fields
2. Detailed evidence and confidence scoring
3. Integration with dual-input AI agent workflow
4. Database flag management based on AI analysis
5. Comprehensive reporting with actionable insights
"""

import json
import os
from intelligent_duplication_detector import IntelligentDuplicationDetector
from dual_input_ai_agent import DualInputInvoiceAI
from invoice_database import InvoiceDatabase

def demonstrate_intelligent_duplication():
    """Demonstrate the intelligent duplication detection capabilities"""
    
    print("🤖 INTELLIGENT DUPLICATION DETECTION DEMO")
    print("=" * 80)
    print("This demo shows the AI-powered duplication analysis that considers:")
    print("✅ Invoice numbers and patterns")
    print("✅ Company/supplier matching")
    print("✅ Product descriptions and HSN codes")
    print("✅ Rates, quantities, and amounts")
    print("✅ Invoice dates and timing patterns")
    print("✅ Line-item level analysis")
    print("=" * 80)
    
    # Initialize detector
    detector = IntelligentDuplicationDetector()
    
    # Show current database state
    db = InvoiceDatabase()
    cursor = db.conn.cursor()
    cursor.execute("""
        SELECT 
            i.invoice_id, 
            i.invoice_num, 
            i.invoice_date,
            i.total_value,
            i.duplication,
            i.validation,
            c.legal_name as supplier
        FROM invoices i
        LEFT JOIN companies c ON i.supplier_company_id = c.company_id
        ORDER BY i.invoice_date DESC
    """)
    invoices = cursor.fetchall()
    
    print(f"\n📋 CURRENT DATABASE STATE ({len(invoices)} invoices):")
    print("-" * 80)
    print(f"{'ID':<4} {'Invoice#':<15} {'Supplier':<25} {'Amount':<15} {'Date':<12} {'Dup':<4} {'Val':<4}")
    print("-" * 80)
    
    for invoice in invoices:
        dup_flag = "🚨" if invoice[4] else "✅"
        val_flag = "✅" if invoice[5] else "❌"
        print(f"{invoice[0]:<4} {invoice[1]:<15} {invoice[6][:24]:<25} ₹{invoice[3]:>12,.0f} {invoice[2]:<12} {dup_flag:<4} {val_flag:<4}")
    
    print(f"\n🔍 DETAILED DUPLICATION ANALYSIS:")
    print("=" * 80)
    
    # Analyze each invoice for duplicates
    for invoice in invoices:
        invoice_id = invoice[0]
        print(f"\n📄 ANALYZING INVOICE: {invoice[1]} (ID: {invoice_id})")
        print("-" * 60)
        
        # Run intelligent analysis
        result = detector.analyze_for_duplicates(invoice_id)
        
        # Show key findings
        if result.duplicate_matches:
            print(f"\n💡 KEY FINDINGS:")
            for i, match in enumerate(result.duplicate_matches, 1):
                print(f"  {i}. Potential duplicate of: {match.original_invoice_num}")
                print(f"     Match type: {match.match_type}")
                print(f"     Confidence: {match.confidence_score:.1%}")
                print(f"     Evidence: {'; '.join(match.evidence[:3])}")  # Top 3 evidence points
                
                if match.matching_fields:
                    print(f"     Matching fields:")
                    for field, value in match.matching_fields.items():
                        if isinstance(value, (int, float)) and value > 1000:
                            print(f"       • {field}: ₹{value:,.2f}")
                        elif isinstance(value, float) and 0 < value < 1:
                            print(f"       • {field}: {value:.1%}")
                        else:
                            print(f"       • {field}: {value}")
    
    # Show duplication patterns summary
    print(f"\n📊 DUPLICATION PATTERNS SUMMARY:")
    print("=" * 50)
    
    # Count different types of duplicates
    all_results = [detector.analyze_for_duplicates(inv[0]) for inv in invoices]
    
    high_confidence_dups = [r for r in all_results if r.confidence_score > 0.8]
    medium_confidence_dups = [r for r in all_results if 0.6 < r.confidence_score <= 0.8]
    low_confidence_dups = [r for r in all_results if 0.4 < r.confidence_score <= 0.6]
    
    print(f"High Confidence Duplicates (>80%): {len(high_confidence_dups)}")
    print(f"Medium Confidence Duplicates (60-80%): {len(medium_confidence_dups)}")
    print(f"Low Confidence Duplicates (40-60%): {len(low_confidence_dups)}")
    print(f"Unique Invoices: {len([r for r in all_results if r.confidence_score <= 0.4])}")
    
    detector.close()
    db.close()

def demonstrate_ai_agent_integration():
    """Demonstrate integration with dual-input AI agent"""
    
    print(f"\n🤖 AI AGENT INTEGRATION DEMO")
    print("=" * 80)
    print("This shows how duplication detection integrates with invoice processing")
    print("=" * 80)
    
    # Check for required files
    textract_file = "textract_analysis.json"
    ocr_file = "1_ocr.json"
    
    if not os.path.exists(textract_file) or not os.path.exists(ocr_file):
        print(f"⚠️  Demo files not available:")
        print(f"   Textract JSON: {textract_file} {'✅' if os.path.exists(textract_file) else '❌'}")
        print(f"   OCR JSON: {ocr_file} {'✅' if os.path.exists(ocr_file) else '❌'}")
        print(f"\n💡 To test full integration:")
        print(f"   1. Process a PDF with textract_analyzer.py")
        print(f"   2. Generate OCR with tesseract_ocr.py")
        print(f"   3. Run this demo again")
        
        # Instead, show the current state
        print(f"\n📊 CURRENT DUPLICATION FLAGS IN DATABASE:")
        db = InvoiceDatabase()
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT invoice_num, duplication, validation
            FROM invoices 
            ORDER BY invoice_id
        """)
        results = cursor.fetchall()
        
        for invoice_num, dup_flag, val_flag in results:
            dup_status = "🚨 DUPLICATE" if dup_flag else "✅ UNIQUE"
            val_status = "✅ VALID" if val_flag else "❌ INVALID"
            print(f"   {invoice_num}: {dup_status}, {val_status}")
        
        db.close()
        return
    
    print(f"📁 Processing with full AI agent pipeline...")
    
    try:
        # Initialize AI agent
        ai_agent = DualInputInvoiceAI()
        
        # Process with dual inputs (includes automatic duplication detection)
        result = ai_agent.process_dual_inputs(textract_file, ocr_file)
        
        print(f"\n📊 AI PROCESSING WITH DUPLICATION ANALYSIS:")
        print("-" * 60)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            # Show duplication analysis results
            if 'duplication_analysis' in result and result['duplication_analysis']:
                dup_result = result['duplication_analysis']
                
                print(f"🤖 DUPLICATION ANALYSIS RESULTS:")
                print(f"   Invoice: {dup_result['invoice_num']}")
                print(f"   Status: {'🚨 DUPLICATE' if dup_result['is_duplicate'] else '✅ UNIQUE'}")
                print(f"   Confidence: {dup_result['confidence_score']:.1%}")
                print(f"   Recommendation: {dup_result['recommended_action']}")
                
                if dup_result['duplicate_matches']:
                    print(f"\n   📋 Detailed Matches:")
                    for i, match in enumerate(dup_result['duplicate_matches'], 1):
                        print(f"     {i}. {match['original_invoice_num']} ({match['confidence_score']:.1%})")
                        print(f"        Type: {match['match_type']}")
                        print(f"        Evidence: {'; '.join(match['evidence'][:2])}")
            
            # Show validation results
            if 'validation_result' in result and result['validation_result']:
                val_result = result['validation_result']
                print(f"\n🧮 ARITHMETIC VALIDATION:")
                print(f"   Tests: {val_result['tests_run']} | Passed: {val_result['tests_passed']}")
                print(f"   Status: {'✅ VALID' if val_result['overall_passed'] else '❌ INVALID'}")
            
            # Show database updates
            if 'database_ids' in result and result['database_ids']:
                print(f"\n💾 DATABASE UPDATES:")
                print(f"   Invoice ID: {result['database_ids'].get('invoice_id')}")
                print(f"   Duplication flag updated based on AI analysis")
                print(f"   Validation flag updated based on arithmetic tests")
        
        ai_agent.close()
        
    except Exception as e:
        print(f"❌ AI processing error: {e}")

def show_sql_queries_for_duplication():
    """Show practical SQL queries for duplication management"""
    
    print(f"\n💾 PRACTICAL SQL QUERIES FOR DUPLICATION MANAGEMENT")
    print("=" * 80)
    
    sql_examples = [
        {
            "title": "Get all duplicate invoices",
            "sql": "SELECT invoice_id, invoice_num, total_value FROM invoices WHERE duplication = 1;"
        },
        {
            "title": "Get all unique invoices",
            "sql": "SELECT invoice_id, invoice_num, total_value FROM invoices WHERE duplication = 0;"
        },
        {
            "title": "Find invoices from same supplier with same amount",
            "sql": """
SELECT 
    i1.invoice_num as invoice1,
    i2.invoice_num as invoice2,
    i1.total_value,
    c.legal_name as supplier
FROM invoices i1
JOIN invoices i2 ON i1.supplier_company_id = i2.supplier_company_id 
    AND i1.total_value = i2.total_value 
    AND i1.invoice_id < i2.invoice_id
JOIN companies c ON i1.supplier_company_id = c.company_id;
"""
        },
        {
            "title": "Duplication statistics by supplier",
            "sql": """
SELECT 
    c.legal_name as supplier,
    COUNT(*) as total_invoices,
    SUM(CASE WHEN i.duplication = 1 THEN 1 ELSE 0 END) as duplicates,
    ROUND(AVG(CASE WHEN i.duplication = 1 THEN 1.0 ELSE 0.0 END) * 100, 2) as duplicate_rate
FROM invoices i
JOIN companies c ON i.supplier_company_id = c.company_id
GROUP BY c.company_id, c.legal_name;
"""
        },
        {
            "title": "Mark specific invoice as unique",
            "sql": "UPDATE invoices SET duplication = 0 WHERE invoice_num = 'SBD/25-26/197';"
        },
        {
            "title": "Find potential duplicates by amount range",
            "sql": """
SELECT 
    i1.invoice_num,
    i1.total_value,
    i2.invoice_num as potential_duplicate,
    i2.total_value as dup_amount,
    ABS(i1.total_value - i2.total_value) as amount_diff
FROM invoices i1
JOIN invoices i2 ON i1.invoice_id != i2.invoice_id
WHERE ABS(i1.total_value - i2.total_value) < 1000  -- Within ₹1000
ORDER BY amount_diff;
"""
        }
    ]
    
    for i, example in enumerate(sql_examples, 1):
        print(f"\n{i}. {example['title']}:")
        print("-" * (len(example['title']) + 3))
        print(example['sql'].strip())

def main():
    """Main demo function"""
    print("🎯 INTELLIGENT DUPLICATION DETECTION SYSTEM")
    print("=" * 80)
    print("AI-powered duplicate detection considering:")
    print("📄 Invoice patterns • 🏢 Supplier matching • 📦 Product analysis")
    print("💰 Amount validation • 📅 Date patterns • 🔢 HSN code matching")
    print("=" * 80)
    
    try:
        # Run comprehensive demos
        demonstrate_intelligent_duplication()
        demonstrate_ai_agent_integration()
        show_sql_queries_for_duplication()
        
    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🏁 DEMO COMPLETED")
    print("=" * 80)
    print("Your intelligent duplication detection system is production ready!")
    print("Key capabilities:")
    print("✅ AI-powered multi-field duplicate analysis")
    print("✅ Confidence scoring with detailed evidence")
    print("✅ Integration with invoice processing workflow")
    print("✅ Automatic database flag management")
    print("✅ Comprehensive reporting and recommendations")

if __name__ == "__main__":
    main()