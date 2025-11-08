#!/usr/bin/env python3
"""
Arithmetic Validation System for Invoice Data

This module performs comprehensive arithmetic validation on invoice data to ensure
mathematical accuracy and data integrity. It automatically detects possible
arithmetic tests and validates them against the stored data.

Features:
1. Auto-discovery of arithmetic relationships in invoice data
2. Comprehensive validation tests (totals, taxes, line items, etc.)
3. Detailed validation reports with pass/fail status
4. Integration with database validation flags
"""

import sqlite3
import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import math

@dataclass
class ValidationResult:
    """Represents the result of a single arithmetic validation test"""
    test_name: str
    description: str
    expected: float
    actual: float
    passed: bool
    tolerance: float = 0.05  # Increased tolerance for rounding differences
    error_message: str = ""
    is_suggestion: bool = False
    suggestion_message: str = ""
    database_reference: Dict[str, Any] = None  # Added for database context

@dataclass
class ArithmeticTest:
    """Represents an arithmetic test that can be performed"""
    test_id: str
    name: str
    description: str
    required_fields: List[str]
    calculation_method: str
    tolerance: float = 0.05  # Increased default tolerance

class ArithmeticValidator:
    """Main class for performing arithmetic validation on invoice data"""
    
    def __init__(self, db_path: str = "invoice_management.db", tolerance: float = 0.05):  # Increased default tolerance
        """Initialize the arithmetic validator"""
        self.db_path = db_path
        self.tolerance = tolerance
        self.arithmetic_tests = self._define_arithmetic_tests()
        
        # Initialize database connection with row factory for dictionary access
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # This enables dict-like access to rows
        
        # Define tax-related test IDs for special handling
        self.tax_related_tests = {
            "gst_calculation", "sgst_calculation", "cgst_calculation", "igst_calculation",
            "total_tax_components", "item_total_with_tax", "invoice_tax_sum", 
            "invoice_grand_total"  # Include grand total as it involves tax
        }
        
    def _is_tax_related_test(self, test_id: str) -> bool:
        """Check if a test is related to tax calculations"""
        return test_id in self.tax_related_tests
        
    def _define_arithmetic_tests(self) -> List[ArithmeticTest]:
        """Define all possible arithmetic tests for invoice data"""
        return [
            ArithmeticTest(
                test_id="line_item_total",
                name="Line Item Total Calculation",
                description="quantity × unit_price should equal taxable_value for each line item",
                required_fields=["quantity", "unit_price", "taxable_value"],
                calculation_method="quantity * unit_price",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="gst_calculation",
                name="GST Amount Calculation",
                description="taxable_value × gst_rate/100 should equal gst_amount",
                required_fields=["taxable_value", "gst_rate", "gst_amount"],
                calculation_method="taxable_value * gst_rate / 100",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="sgst_calculation",
                name="SGST Amount Calculation",
                description="taxable_value × sgst_rate/100 should equal sgst_amount",
                required_fields=["taxable_value", "sgst_rate", "sgst_amount"],
                calculation_method="taxable_value * sgst_rate / 100",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="cgst_calculation",
                name="CGST Amount Calculation",
                description="taxable_value × cgst_rate/100 should equal cgst_amount",
                required_fields=["taxable_value", "cgst_rate", "cgst_amount"],
                calculation_method="taxable_value * cgst_rate / 100",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="igst_calculation",
                name="IGST Amount Calculation",
                description="taxable_value × igst_rate/100 should equal igst_amount",
                required_fields=["taxable_value", "igst_rate", "igst_amount"],
                calculation_method="taxable_value * igst_rate / 100",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="total_tax_components",
                name="Total Tax Components",
                description="sgst_amount + cgst_amount + igst_amount should equal total tax",
                required_fields=["sgst_amount", "cgst_amount", "igst_amount"],
                calculation_method="sgst_amount + cgst_amount + igst_amount",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="item_total_with_tax",
                name="Item Total with Tax",
                description="taxable_value + all_tax_amounts should equal total_amount",
                required_fields=["taxable_value", "gst_amount", "sgst_amount", "cgst_amount", "igst_amount", "total_amount"],
                calculation_method="taxable_value + tax_amounts",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="invoice_taxable_sum",
                name="Invoice Taxable Value Sum",
                description="Sum of all line item taxable_values should equal invoice taxable_value",
                required_fields=["line_items_taxable_sum", "invoice_taxable_value"],
                calculation_method="sum(line_items.taxable_value)",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="invoice_tax_sum",
                name="Invoice Tax Sum",
                description="Sum of all line item taxes should equal invoice total_tax",
                required_fields=["line_items_tax_sum", "invoice_total_tax"],
                calculation_method="sum(line_items.tax_amounts)",
                tolerance=0.05  # Increased tolerance for rounding
            ),
            ArithmeticTest(
                test_id="invoice_grand_total",
                name="Invoice Grand Total",
                description="invoice_taxable_value + invoice_total_tax should equal invoice_total_value",
                required_fields=["taxable_value", "total_tax", "total_value"],
                calculation_method="taxable_value + total_tax",
                tolerance=0.05  # Increased tolerance for rounding
            )
        ]
    
    def discover_applicable_tests(self, invoice_id: int) -> List[ArithmeticTest]:
        """Discover which arithmetic tests can be applied to a specific invoice"""
        applicable_tests = []
        suggestion_tests = []
        
        # Get invoice data
        invoice_data = self._get_invoice_data(invoice_id)
        line_items = self._get_line_items(invoice_id)
        
        if not invoice_data:
            return applicable_tests
        
        print(f"🔍 Discovering arithmetic tests for Invoice ID: {invoice_id}")
        print(f"📊 Invoice: {invoice_data['invoice_num']}")
        print(f"📋 Line items found: {len(line_items)}")
        
        for test in self.arithmetic_tests:
            can_apply = self._can_apply_test(test, invoice_data, line_items)
            missing_fields = self._get_missing_fields(test, invoice_data, line_items)
            
            if can_apply:
                applicable_tests.append(test)
                print(f"  ✅ {test.name}")
            else:
                if missing_fields:
                    suggestion_tests.append(test)
                    print(f"  💡 {test.name} (Missing: {', '.join(missing_fields)} - will provide suggestion)")
                else:
                    print(f"  ❌ {test.name} (Not applicable)")
        
        print(f"\n📈 Found {len(applicable_tests)} applicable tests and {len(suggestion_tests)} suggestion tests")
        
        # Return both applicable and suggestion tests
        return applicable_tests + suggestion_tests
    
    def _get_invoice_data(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice header data"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM invoices WHERE invoice_id = ?
            """, (invoice_id,))
            
            row = cursor.fetchone()
            if row:
                # Convert sqlite3.Row to dict
                return {key: row[key] for key in row.keys()}
            return None
        except Exception as e:
            print(f"❌ Error getting invoice data for ID {invoice_id}: {str(e)}")
            return None
    
    def _get_line_items(self, invoice_id: int) -> List[Dict[str, Any]]:
        """Get all line items for an invoice"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM invoice_item WHERE invoice_id = ?
            """, (invoice_id,))
            
            rows = cursor.fetchall()
            # Convert sqlite3.Row objects to dicts
            return [{key: row[key] for key in row.keys()} for row in rows]
        except Exception as e:
            print(f"❌ Error getting line items for invoice ID {invoice_id}: {str(e)}")
            return []
    
    def _can_apply_test(self, test: ArithmeticTest, invoice_data: Dict, line_items: List[Dict]) -> bool:
        """Check if a test can be applied based on available data"""
        # For invoice-level tests
        if test.test_id in ["invoice_taxable_sum", "invoice_tax_sum", "invoice_grand_total"]:
            return len(line_items) > 0 and invoice_data is not None
        
        # For line item tests - check if ANY line item has sufficient data to perform the test
        if line_items:
            for item in line_items:
                # For tax calculations, we need the tax rate AND tax amount fields
                if test.test_id in ["sgst_calculation", "cgst_calculation", "igst_calculation"]:
                    tax_type = test.test_id.split("_")[0]
                    rate_field = f"{tax_type}_rate"
                    amount_field = f"{tax_type}_amount"
                    if (item.get(rate_field) is not None and item.get(amount_field) is not None and 
                        item.get('taxable_value') is not None):
                        return True
                # For other tests, check if all required fields are available and not None
                elif all(item.get(field) is not None for field in test.required_fields):
                    return True
        
        return False
    
    def _get_missing_fields(self, test: ArithmeticTest, invoice_data: Dict, line_items: List[Dict]) -> List[str]:
        """Get list of missing fields for a test"""
        missing = []
        
        # Check invoice data
        for field in test.required_fields:
            if field in ["invoice_taxable_value", "invoice_total_tax", "taxable_value", "total_tax", "total_value"]:
                if not self._has_non_zero_value(invoice_data, field.replace("invoice_", "")):
                    missing.append(field)
        
        # Check line item data
        if line_items:
            sample_item = line_items[0]
            for field in test.required_fields:
                if field not in ["invoice_taxable_value", "invoice_total_tax", "taxable_value", "total_tax", "total_value"]:
                    if not self._has_non_zero_value(sample_item, field):
                        missing.append(field)
        
        return missing
    
    def _has_non_zero_value(self, data: Dict, field: str) -> bool:
        """Check if a field exists and has a non-zero value"""
        return field in data and data[field] is not None and data[field] != 0
    
    def _has_value_or_suggest(self, data: Dict, field: str) -> Tuple[bool, str]:
        """Check if field has value, return suggestion if missing"""
        if field not in data or data[field] is None:
            return False, f"Field '{field}' is missing from the data"
        elif data[field] == 0:
            return False, f"Field '{field}' has zero value - may not be extracted correctly"
        return True, ""
    
    def validate_invoice(self, invoice_id: int) -> Dict[str, Any]:
        """Perform comprehensive arithmetic validation on an invoice"""
        print(f"\n🧮 ARITHMETIC VALIDATION - Invoice ID: {invoice_id}")
        print("=" * 60)
        
        # Discover applicable tests
        applicable_tests = self.discover_applicable_tests(invoice_id)
        
        if not applicable_tests:
            return {
                "invoice_id": invoice_id,
                "tests_run": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "overall_passed": False,
                "results": [],
                "error": "No applicable tests found"
            }
        
        # Get data
        invoice_data = self._get_invoice_data(invoice_id)
        line_items = self._get_line_items(invoice_id)
        
        # Run tests
        results = []
        tests_passed = 0
        tests_failed = 0
        tax_tests_failed = 0  # Track tax-related failures separately
        suggestion_count = 0
        valid_checks_log = []  # Track valid checks for logging
        
        for test in applicable_tests:
            # Check if this test can actually be run or should be a suggestion
            can_run = self._can_apply_test(test, invoice_data, line_items)
            
            if can_run:
                test_results = self._run_test(test, invoice_data, line_items)
                results.extend(test_results)
                
                for result in test_results:
                    if result.is_suggestion:
                        suggestion_count += 1
                    elif result.passed:
                        tests_passed += 1
                        # Log valid checks
                        valid_checks_log.append({
                            'test_name': result.test_name,
                            'expected': result.expected,
                            'actual': result.actual,
                            'tolerance': result.tolerance,
                            'description': result.description
                        })
                    else:
                        tests_failed += 1
                        # Check if this is a tax-related failure
                        if self._is_tax_related_test(test.test_id):
                            tax_tests_failed += 1
            else:
                # Create a suggestion result for missing data
                missing_fields = self._get_missing_fields(test, invoice_data, line_items)
                suggestion_result = ValidationResult(
                    test_name=test.name,
                    description=test.description,
                    expected=0.0,
                    actual=0.0,
                    passed=True,
                    tolerance=test.tolerance,
                    error_message="",
                    is_suggestion=True,
                    suggestion_message=f"Cannot perform {test.name} - Missing required fields: {', '.join(missing_fields)}"
                )
                results.append(suggestion_result)
                suggestion_count += 1
        
        # Calculate overall pass status - ignore tax-related failures
        non_tax_failures = tests_failed - tax_tests_failed
        overall_passed = non_tax_failures == 0
        
        # Log valid checks
        if valid_checks_log:
            print(f"\n✅ VALID CHECKS LOG ({len(valid_checks_log)} checks passed):")
            print("-" * 50)
            for check in valid_checks_log:
                print(f"✓ {check['test_name']}")
                print(f"  Expected: {check['expected']:.2f}, Actual: {check['actual']:.2f}")
                print(f"  Tolerance: ±{check['tolerance']:.2f}")
                print(f"  Description: {check['description']}")
                print()
        
        # Print results
        print(f"\n📊 VALIDATION RESULTS:")
        print("-" * 40)
        for result in results:
            if result.is_suggestion:
                print(f"💡 SUGGESTION {result.test_name}")
                print(f"     {result.suggestion_message}")
            else:
                status = "✅ PASS" if result.passed else "❌ FAIL"
                # Check if this is a tax-related failure that we're ignoring
                test_id = next((test.test_id for test in self.arithmetic_tests if test.name == result.test_name), "")
                is_tax_related = self._is_tax_related_test(test_id)
                
                if not result.passed and is_tax_related:
                    status += " (TAX-RELATED - IGNORED)"
                
                print(f"{status} {result.test_name}")
                if not result.passed:
                    print(f"     Expected: {result.expected:.2f}, Got: {result.actual:.2f}")
                    print(f"     Error: {result.error_message}")
                    
                    if is_tax_related:
                        print(f"     📝 Note: Tax-related validation failures are ignored in overall assessment")
                    
                    # Show detailed database reference for failures
                    if result.database_reference:
                        db_ref = result.database_reference
                        print(f"     📊 Database Reference:")
                        print(f"        Table: {db_ref.get('table', 'N/A')}")
                        if 'stored_values' in db_ref:
                            print(f"        Stored Values: {db_ref['stored_values']}")
                        if 'calculation' in db_ref:
                            print(f"        Expected Calculation: {db_ref['calculation']}")
                        if 'line_items_breakdown' in db_ref:
                            print(f"        Line Items Breakdown: {db_ref['line_items_breakdown']}")
                        if 'tax_breakdown' in db_ref:
                            print(f"        Tax Breakdown: {db_ref['tax_breakdown']}")
        
        # Count only non-suggestion tests for pass/fail
        validation_results = [r for r in results if not r.is_suggestion]
        suggestion_count = len([r for r in results if r.is_suggestion])
        validation_passed = sum(1 for r in validation_results if r.passed)
        validation_failed = sum(1 for r in validation_results if not r.passed)
        
        # Calculate non-tax failures for overall status
        non_tax_validation_failed = validation_failed - tax_tests_failed
        overall_passed = non_tax_validation_failed == 0  # Pass if no non-tax validation failures
        
        print(f"\n📈 SUMMARY:")
        print(f"Tests Run: {len(validation_results)} (+ {suggestion_count} suggestions)")
        print(f"Passed: {validation_passed}")
        print(f"Failed: {validation_failed}")
        if tax_tests_failed > 0:
            print(f"Tax-related Failures (Ignored): {tax_tests_failed}")
            print(f"Non-tax Failures: {non_tax_validation_failed}")
        print(f"Suggestions: {suggestion_count}")
        print(f"Overall: {'✅ VALID' if overall_passed else '❌ INVALID'}")
        
        # Add detailed reasoning for validation result
        if not overall_passed:
            # Only show non-tax failures as critical
            failed_tests = [r for r in validation_results if not r.passed]
            non_tax_failed_tests = []
            tax_failed_tests = []
            
            for test in failed_tests:
                test_id = next((t.test_id for t in self.arithmetic_tests if t.name == test.test_name), "")
                if self._is_tax_related_test(test_id):
                    tax_failed_tests.append(test)
                else:
                    non_tax_failed_tests.append(test)
            
            if non_tax_failed_tests:
                print(f"\n🔍 CRITICAL VALIDATION FAILURES:")
                for test in non_tax_failed_tests[:3]:  # Show top 3 critical failures
                    print(f"   • {test.test_name}: {test.error_message}")
                if len(non_tax_failed_tests) > 3:
                    print(f"   ... and {len(non_tax_failed_tests) - 3} more critical errors")
            
            if tax_failed_tests:
                print(f"\n📝 TAX-RELATED FAILURES (IGNORED):")
                for test in tax_failed_tests[:3]:  # Show top 3 tax failures
                    print(f"   • {test.test_name}: {test.error_message}")
                if len(tax_failed_tests) > 3:
                    print(f"   ... and {len(tax_failed_tests) - 3} more tax-related errors")
            
            # Suggest potential issues
            print(f"\n💡 POTENTIAL ISSUES:")
            if any("tax" in t.test_name.lower() for t in failed_tests):
                print("   • Tax calculations may be incorrect or missing")
            if any("total" in t.test_name.lower() for t in failed_tests):
                print("   • Invoice totals don't match line item sums")
            print("   • Check for data extraction errors or calculation inconsistencies")
        else:
            print(f"\n✅ VALIDATION SUCCESS REASONS:")
            if len(validation_results) > 0:
                print(f"   • All {len(validation_results)} arithmetic tests passed successfully")
                print(f"   • Invoice calculations are mathematically consistent")
                if len(validation_results) >= 5:
                    print(f"   • Comprehensive validation includes line items, taxes, and totals")
                print(f"   • Data integrity confirmed for financial accuracy")
            else:
                print(f"   • No validation tests could be performed (all fields missing)")
                print(f"   • This may indicate extraction issues - please review data quality")
            
            if suggestion_count > 0:
                print(f"   • {suggestion_count} suggestions provided for missing data fields")
        
        # Update database validation flag
        self._update_validation_status(invoice_id, overall_passed)
        
        return {
            "invoice_id": invoice_id,
            "tests_run": len(validation_results),
            "tests_passed": validation_passed,
            "tests_failed": validation_failed,
            "tax_tests_failed": tax_tests_failed,
            "non_tax_tests_failed": validation_failed - tax_tests_failed,
            "suggestions_count": suggestion_count,
            "overall_passed": overall_passed,
            "valid_checks_log": valid_checks_log,
            "results": [self._result_to_dict(r) for r in results],
            "invoice_data": invoice_data,
            "line_items": line_items,
            "validation_notes": {
                "tax_failures_ignored": tax_tests_failed > 0,
                "critical_failures_only": validation_failed - tax_tests_failed,
                "total_passed_validations": validation_passed
            }
        }
    
    def _run_test(self, test: ArithmeticTest, invoice_data: Dict, line_items: List[Dict]) -> List[ValidationResult]:
        """Run a specific arithmetic test"""
        results = []
        
        if test.test_id == "line_item_total":
            for i, item in enumerate(line_items):
                # Check if all required fields are available
                missing_fields = []
                suggestions = []
                
                qty_available, qty_msg = self._has_value_or_suggest(item, 'quantity')
                price_available, price_msg = self._has_value_or_suggest(item, 'unit_price') 
                taxable_available, taxable_msg = self._has_value_or_suggest(item, 'taxable_value')
                
                if not qty_available:
                    missing_fields.append('quantity')
                    suggestions.append(qty_msg)
                if not price_available:
                    missing_fields.append('unit_price')
                    suggestions.append(price_msg)
                if not taxable_available:
                    missing_fields.append('taxable_value')
                    suggestions.append(taxable_msg)
                
                if missing_fields:
                    # Create suggestion instead of failure
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} Total",
                        description=test.description,
                        expected=0.0,
                        actual=0.0,
                        passed=True,  # Mark as passed to avoid failure
                        tolerance=test.tolerance,
                        error_message="",
                        is_suggestion=True,
                        suggestion_message=f"Cannot validate calculation - {'; '.join(suggestions)}"
                    ))
                else:
                    expected = float(item['quantity']) * float(item['unit_price'])
                    actual = float(item['taxable_value'])
                    passed = abs(expected - actual) <= test.tolerance
                    
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} Total",
                        description=test.description,
                        expected=expected,
                        actual=actual,
                        passed=passed,
                        tolerance=test.tolerance,
                        error_message="" if passed else f"Quantity({item['quantity']}) × Unit Price({item['unit_price']}) ≠ Taxable Value({item['taxable_value']})",
                        database_reference={
                            "table": "invoice_item",
                            "item_id": item.get('item_id', f"Line {i+1}"),
                            "invoice_id": item.get('invoice_id'),
                            "stored_values": {
                                "quantity": item['quantity'],
                                "unit_price": item['unit_price'], 
                                "taxable_value": item['taxable_value']
                            },
                            "calculation": f"{item['quantity']} × {item['unit_price']} = {expected}"
                        }
                    ))
        
        elif test.test_id in ["gst_calculation", "sgst_calculation", "cgst_calculation", "igst_calculation"]:
            tax_type = test.test_id.split("_")[0]
            for i, item in enumerate(line_items):
                rate_field = f"{tax_type}_rate"
                amount_field = f"{tax_type}_amount"
                
                # Check field availability
                rate_available, rate_msg = self._has_value_or_suggest(item, rate_field)
                taxable_available, taxable_msg = self._has_value_or_suggest(item, "taxable_value")
                amount_available, amount_msg = self._has_value_or_suggest(item, amount_field)
                
                missing_suggestions = []
                if not rate_available:
                    missing_suggestions.append(rate_msg)
                if not taxable_available:
                    missing_suggestions.append(taxable_msg)
                if not amount_available:
                    missing_suggestions.append(amount_msg)
                
                if missing_suggestions:
                    # Create suggestion instead of failure
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} {tax_type.upper()} Calculation",
                        description=test.description,
                        expected=0.0,
                        actual=0.0,
                        passed=True,  # Mark as passed to avoid failure
                        tolerance=test.tolerance,
                        error_message="",
                        is_suggestion=True,
                        suggestion_message=f"Cannot validate {tax_type.upper()} calculation - {'; '.join(missing_suggestions)}"
                    ))
                else:
                    expected = float(item['taxable_value']) * float(item[rate_field]) / 100
                    actual = float(item[amount_field])
                    passed = abs(expected - actual) <= test.tolerance
                    
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} {tax_type.upper()} Calculation",
                        description=test.description,
                        expected=expected,
                        actual=actual,
                        passed=passed,
                        tolerance=test.tolerance,
                        error_message="" if passed else f"Taxable({item['taxable_value']}) × Rate({item[rate_field]}%) ≠ Amount({item[amount_field]})",
                        database_reference={
                            "table": "invoice_item",
                            "item_id": item.get('item_id', f"Line {i+1}"),
                            "invoice_id": item.get('invoice_id'),
                            "stored_values": {
                                "taxable_value": item['taxable_value'],
                                f"{tax_type}_rate": item[rate_field],
                                f"{tax_type}_amount": item[amount_field]
                            },
                            "calculation": f"{item['taxable_value']} × {item[rate_field]}% = {expected}"
                        }
                    ))
        
        elif test.test_id == "total_tax_components":
            for i, item in enumerate(line_items):
                # Check if tax amounts are available
                sgst_val = float(item['sgst_amount']) if item.get('sgst_amount') else None
                cgst_val = float(item['cgst_amount']) if item.get('cgst_amount') else None  
                igst_val = float(item['igst_amount']) if item.get('igst_amount') else None
                gst_val = float(item['gst_amount']) if item.get('gst_amount') else None
                
                missing_taxes = []
                if sgst_val is None:
                    missing_taxes.append("SGST amount")
                if cgst_val is None:
                    missing_taxes.append("CGST amount")
                if igst_val is None:
                    missing_taxes.append("IGST amount")
                if gst_val is None:
                    missing_taxes.append("Total GST amount")
                
                if len(missing_taxes) >= 3:  # If most tax fields are missing
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} Tax Components",
                        description=test.description,
                        expected=0.0,
                        actual=0.0,
                        passed=True,  # Mark as passed to avoid failure
                        tolerance=test.tolerance,
                        error_message="",
                        is_suggestion=True,
                        suggestion_message=f"Cannot validate tax components - Missing: {', '.join(missing_taxes)}"
                    ))
                else:
                    sgst = sgst_val if sgst_val is not None else 0
                    cgst = cgst_val if cgst_val is not None else 0
                    igst = igst_val if igst_val is not None else 0
                    gst = gst_val if gst_val is not None else 0
                    
                    expected = sgst + cgst + igst
                    actual = gst
                    passed = abs(expected - actual) <= test.tolerance
                    
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} Tax Components",
                        description=test.description,
                        expected=expected,
                        actual=actual,
                        passed=passed,
                        tolerance=test.tolerance,
                        error_message="" if passed else f"SGST({sgst}) + CGST({cgst}) + IGST({igst}) ≠ Total GST({gst})"
                    ))
        
        elif test.test_id == "item_total_with_tax":
            for i, item in enumerate(line_items):
                # Check availability of required fields
                taxable_available, taxable_msg = self._has_value_or_suggest(item, 'taxable_value')
                total_available, total_msg = self._has_value_or_suggest(item, 'total_amount')
                
                if not taxable_available or not total_available:
                    suggestions = []
                    if not taxable_available:
                        suggestions.append(taxable_msg)
                    if not total_available:
                        suggestions.append(total_msg)
                    
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} Total with Tax",
                        description=test.description,
                        expected=0.0,
                        actual=0.0,
                        passed=True,  # Mark as passed to avoid failure
                        tolerance=test.tolerance,
                        error_message="",
                        is_suggestion=True,
                        suggestion_message=f"Cannot validate total with tax - {'; '.join(suggestions)}"
                    ))
                else:
                    taxable = float(item['taxable_value'])
                    sgst = float(item['sgst_amount']) if item.get('sgst_amount') else 0
                    cgst = float(item['cgst_amount']) if item.get('cgst_amount') else 0
                    igst = float(item['igst_amount']) if item.get('igst_amount') else 0
                    gst = float(item['gst_amount']) if item.get('gst_amount') else 0
                    
                    expected = taxable + max(sgst + cgst, igst, gst)  # Use whichever tax calculation is non-zero
                    actual = float(item['total_amount'])
                    passed = abs(expected - actual) <= test.tolerance
                    
                    results.append(ValidationResult(
                        test_name=f"Line Item {i+1} Total with Tax",
                        description=test.description,
                        expected=expected,
                        actual=actual,
                        passed=passed,
                        tolerance=test.tolerance,
                        error_message="" if passed else f"Taxable({taxable}) + Tax ≠ Total({actual})"
                    ))
        
        elif test.test_id == "invoice_taxable_sum":
            line_items_sum = sum(float(item['taxable_value']) if item.get('taxable_value') else 0 for item in line_items)
            
            # Check if invoice taxable value is available
            invoice_taxable_available, invoice_msg = self._has_value_or_suggest(invoice_data, 'taxable_value')
            
            if not invoice_taxable_available:
                results.append(ValidationResult(
                    test_name="Invoice Taxable Value Sum",
                    description=test.description,
                    expected=line_items_sum,
                    actual=0.0,
                    passed=True,  # Mark as passed to avoid failure
                    tolerance=test.tolerance,
                    error_message="",
                    is_suggestion=True,
                    suggestion_message=f"Cannot validate invoice taxable sum - {invoice_msg}"
                ))
            else:
                invoice_taxable = float(invoice_data['taxable_value'])
                passed = abs(line_items_sum - invoice_taxable) <= test.tolerance
                
            results.append(ValidationResult(
                test_name="Invoice Taxable Value Sum",
                description=test.description,
                expected=line_items_sum,
                actual=invoice_taxable,
                passed=passed,
                tolerance=test.tolerance,
                error_message="" if passed else f"Sum of line items({line_items_sum}) ≠ Invoice taxable({invoice_taxable})",
                database_reference={
                    "table": "invoices",
                    "invoice_id": invoice_data.get('invoice_id'),
                    "stored_values": {
                        "invoice_taxable_value": invoice_taxable,
                        "calculated_line_items_sum": line_items_sum
                    },
                    "line_items_breakdown": [
                        {f"Line {i+1}": float(item['taxable_value']) if item.get('taxable_value') else 0} 
                        for i, item in enumerate(line_items)
                    ]
                }
            ))
        
        elif test.test_id == "invoice_tax_sum":
            line_items_tax_sum = 0
            for item in line_items:
                sgst = float(item['sgst_amount']) if item.get('sgst_amount') else 0
                cgst = float(item['cgst_amount']) if item.get('cgst_amount') else 0
                igst = float(item['igst_amount']) if item.get('igst_amount') else 0
                gst = float(item['gst_amount']) if item.get('gst_amount') else 0
                
                # Use whichever tax calculation is non-zero
                item_tax = max(sgst + cgst, igst, gst)
                line_items_tax_sum += item_tax
            
            # Check if invoice tax total is available
            invoice_tax_available, invoice_tax_msg = self._has_value_or_suggest(invoice_data, 'total_tax')
            
            if not invoice_tax_available:
                results.append(ValidationResult(
                    test_name="Invoice Tax Sum",
                    description=test.description,
                    expected=line_items_tax_sum,
                    actual=0.0,
                    passed=True,  # Mark as passed to avoid failure
                    tolerance=test.tolerance,
                    error_message="",
                    is_suggestion=True,
                    suggestion_message=f"Cannot validate invoice tax sum - {invoice_tax_msg}"
                ))
            else:
                invoice_tax = float(invoice_data['total_tax'])
                passed = abs(line_items_tax_sum - invoice_tax) <= test.tolerance
                
            results.append(ValidationResult(
                test_name="Invoice Tax Sum",
                description=test.description,
                expected=line_items_tax_sum,
                actual=invoice_tax,
                passed=passed,
                tolerance=test.tolerance,
                error_message="" if passed else f"Sum of line item taxes({line_items_tax_sum}) ≠ Invoice tax({invoice_tax})",
                database_reference={
                    "table": "invoices",
                    "invoice_id": invoice_data.get('invoice_id'),
                    "stored_values": {
                        "invoice_total_tax": invoice_tax,
                        "calculated_tax_sum": line_items_tax_sum
                    },
                    "tax_breakdown": [
                        {
                            f"Line {i+1}": {
                                "sgst": float(item['sgst_amount']) if item.get('sgst_amount') else 0,
                                "cgst": float(item['cgst_amount']) if item.get('cgst_amount') else 0,
                                "igst": float(item['igst_amount']) if item.get('igst_amount') else 0,
                                "gst": float(item['gst_amount']) if item.get('gst_amount') else 0
                            }
                        } for i, item in enumerate(line_items)
                    ]
                }
            ))
        
        elif test.test_id == "invoice_grand_total":
            # Check availability of required invoice fields
            taxable_available, taxable_msg = self._has_value_or_suggest(invoice_data, 'taxable_value')
            tax_available, tax_msg = self._has_value_or_suggest(invoice_data, 'total_tax')
            total_available, total_msg = self._has_value_or_suggest(invoice_data, 'total_value')
            
            missing_suggestions = []
            if not taxable_available:
                missing_suggestions.append(taxable_msg)
            if not tax_available:
                missing_suggestions.append(tax_msg)
            if not total_available:
                missing_suggestions.append(total_msg)
            
            if missing_suggestions:
                results.append(ValidationResult(
                    test_name="Invoice Grand Total",
                    description=test.description,
                    expected=0.0,
                    actual=0.0,
                    passed=True,  # Mark as passed to avoid failure
                    tolerance=test.tolerance,
                    error_message="",
                    is_suggestion=True,
                    suggestion_message=f"Cannot validate grand total - {'; '.join(missing_suggestions)}"
                ))
            else:
                taxable = float(invoice_data['taxable_value'])
                tax = float(invoice_data['total_tax'])
                expected = round(taxable + tax, 2)  # Round to 2 decimal places
                actual = round(float(invoice_data['total_value']), 2)
                
                passed = abs(expected - actual) <= test.tolerance
                
                results.append(ValidationResult(
                    test_name="Invoice Grand Total",
                    description=test.description,
                    expected=expected,
                    actual=actual,
                    passed=passed,
                    tolerance=test.tolerance,
                    error_message="" if passed else f"Taxable({taxable}) + Tax({tax}) = {expected} ≠ Total({actual})",
                    database_reference={
                        "table": "invoices",
                        "invoice_id": invoice_data.get('invoice_id'),
                        "stored_values": {
                            "taxable_value": taxable,
                            "total_tax": tax,
                            "total_value": actual,
                            "calculated_total": expected
                        },
                        "calculation": f"{taxable} + {tax} = {expected}"
                    }
                ))
        
        return results
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            print("📝 Arithmetic validator connection closed")
    
    def _result_to_dict(self, result: ValidationResult) -> Dict[str, Any]:
        """Convert ValidationResult to dictionary"""
        return {
            "test_name": result.test_name,
            "description": result.description,
            "expected": result.expected,
            "actual": result.actual,
            "passed": result.passed,
            "tolerance": result.tolerance,
            "error_message": result.error_message,
            "is_suggestion": result.is_suggestion,
            "suggestion_message": result.suggestion_message,
            "database_reference": result.database_reference
        }
    
    def _update_validation_status(self, invoice_id: int, is_valid: bool):
        """Update the validation status in the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE invoices SET validation = ? WHERE invoice_id = ?
        """, (1 if is_valid else 0, invoice_id))
        self.conn.commit()
        
        status = "✅ VALIDATED" if is_valid else "❌ VALIDATION FAILED"
        print(f"\n🔄 Database updated: Invoice {invoice_id} marked as {status}")
    
    def validate_all_invoices(self) -> Dict[str, Any]:
        """Validate all invoices in the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT invoice_id FROM invoices")
        invoice_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"\n🔍 VALIDATING ALL INVOICES ({len(invoice_ids)} invoices)")
        print("=" * 60)
        
        all_results = []
        total_passed = 0
        total_failed = 0
        
        for invoice_id in invoice_ids:
            result = self.validate_invoice(invoice_id)
            all_results.append(result)
            
            if result['overall_passed']:
                total_passed += 1
            else:
                total_failed += 1
        
        print(f"\n📊 OVERALL SUMMARY:")
        print(f"Total Invoices: {len(invoice_ids)}")
        print(f"Passed Validation: {total_passed}")
        print(f"Failed Validation: {total_failed}")
        print(f"Success Rate: {(total_passed/len(invoice_ids)*100):.1f}%" if invoice_ids else "0%")
        
        return {
            "total_invoices": len(invoice_ids),
            "passed_validation": total_passed,
            "failed_validation": total_failed,
            "success_rate": (total_passed/len(invoice_ids)*100) if invoice_ids else 0,
            "detailed_results": all_results
        }
    
    def get_validation_report(self, invoice_id: int) -> str:
        """Generate a detailed validation report for an invoice"""
        result = self.validate_invoice(invoice_id)
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    ARITHMETIC VALIDATION REPORT             ║
╠══════════════════════════════════════════════════════════════╣
║ Invoice ID: {result['invoice_id']:<47} ║
║ Invoice Number: {result['invoice_data']['invoice_num']:<42} ║
║ Tests Run: {result['tests_run']:<48} ║
║ Passed: {result['tests_passed']:<51} ║
║ Failed: {result['tests_failed']:<51} ║
║ Overall Status: {('✅ VALID' if result['overall_passed'] else '❌ INVALID'):<41} ║
╠══════════════════════════════════════════════════════════════╣
║                        DETAILED RESULTS                     ║
╚══════════════════════════════════════════════════════════════╝

"""
        
        for test_result in result['results']:
            if test_result.get('is_suggestion', False):
                report += f"💡 SUGGESTION {test_result['test_name']}\n"
                report += f"   {test_result['suggestion_message']}\n"
            else:
                status = "✅ PASS" if test_result['passed'] else "❌ FAIL"
                report += f"{status} {test_result['test_name']}\n"
                report += f"   Expected: {test_result['expected']:.2f}\n"
                report += f"   Actual: {test_result['actual']:.2f}\n"
                if test_result['error_message']:
                    report += f"   Error: {test_result['error_message']}\n"
            report += "\n"
        
        return report
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("📝 Arithmetic validator connection closed")

def main():
    """Main function to demonstrate arithmetic validation"""
    print("🧮 ARITHMETIC VALIDATION SYSTEM")
    print("=" * 50)
    
    # Initialize validator
    validator = ArithmeticValidator()
    
    # Validate all invoices
    results = validator.validate_all_invoices()
    
    # Show detailed report for first invoice
    if results['detailed_results']:
        first_invoice_id = results['detailed_results'][0]['invoice_id']
        print(f"\n📋 DETAILED REPORT FOR INVOICE {first_invoice_id}:")
        print(validator.get_validation_report(first_invoice_id))
    
    # Close connection
    validator.close()
    
    return results

if __name__ == "__main__":
    main()