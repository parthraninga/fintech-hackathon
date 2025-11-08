#!/usr/bin/env python3
"""
Database Reporter - Detailed Database Insertion Information

This module provides comprehensive reporting of database insertions after document processing.
It shows exactly what data was inserted into which tables and fields.
"""

import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from invoice_database import InvoiceDatabase

class DatabaseReporter:
    """Generate detailed reports of database insertions"""
    
    def __init__(self, db_path: str = "invoice_management.db"):
        self.db = InvoiceDatabase(db_path)
        self.table_schemas = {
            "documents": {
                "name": "Documents Table",
                "description": "Document metadata for uploaded files",
                "fields": [
                    {"name": "doc_id", "type": "INTEGER", "description": "Unique document identifier"},
                    {"name": "doc_type", "type": "VARCHAR(50)", "description": "Document type (INVOICE, RECEIPT)"},
                    {"name": "filename", "type": "VARCHAR(255)", "description": "Original filename"},
                    {"name": "file_size_bytes", "type": "INTEGER", "description": "File size in bytes"},
                    {"name": "analysis_confidence", "type": "DECIMAL(5,2)", "description": "AI confidence score (0-100)"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"},
                    {"name": "raw_data", "type": "TEXT", "description": "Original OCR JSON data"}
                ]
            },
            "companies": {
                "name": "Companies Table", 
                "description": "Company master data with GST information",
                "fields": [
                    {"name": "company_id", "type": "INTEGER", "description": "Unique company identifier"},
                    {"name": "legal_name", "type": "VARCHAR(255)", "description": "Official company name"},
                    {"name": "gstin", "type": "VARCHAR(15)", "description": "GST Identification Number"},
                    {"name": "city", "type": "VARCHAR(100)", "description": "Company city"},
                    {"name": "state", "type": "VARCHAR(50)", "description": "Company state"},
                    {"name": "address", "type": "TEXT", "description": "Complete address"},
                    {"name": "phone", "type": "VARCHAR(20)", "description": "Contact phone"},
                    {"name": "email", "type": "VARCHAR(100)", "description": "Contact email"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"}
                ]
            },
            "gst_companies": {
                "name": "GST Companies Table",
                "description": "Validated GST data from government APIs",
                "fields": [
                    {"name": "gst_id", "type": "INTEGER", "description": "Unique GST record ID"},
                    {"name": "gstin", "type": "VARCHAR(15)", "description": "GST Identification Number"},
                    {"name": "legal_name", "type": "VARCHAR(255)", "description": "Official legal name"},
                    {"name": "trade_name", "type": "VARCHAR(255)", "description": "Trade/business name"},
                    {"name": "pan", "type": "VARCHAR(10)", "description": "PAN Number"},
                    {"name": "registration_date", "type": "VARCHAR(20)", "description": "GST registration date"},
                    {"name": "constitution", "type": "VARCHAR(100)", "description": "Business constitution"},
                    {"name": "taxpayer_type", "type": "VARCHAR(50)", "description": "Taxpayer classification"},
                    {"name": "status", "type": "VARCHAR(20)", "description": "GST status (Active/Cancelled)"},
                    {"name": "state", "type": "VARCHAR(50)", "description": "Registered state"},
                    {"name": "pin_code", "type": "VARCHAR(10)", "description": "PIN code"},
                    {"name": "api_source", "type": "VARCHAR(50)", "description": "Validation API source"},
                    {"name": "last_verified", "type": "TIMESTAMP", "description": "Last verification time"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"}
                ]
            },
            "products": {
                "name": "Products Table",
                "description": "Product catalog with HSN codes and tax rates",
                "fields": [
                    {"name": "product_id", "type": "INTEGER", "description": "Unique product identifier"},
                    {"name": "canonical_name", "type": "VARCHAR(255)", "description": "Standardized product name"},
                    {"name": "hsn_code", "type": "VARCHAR(10)", "description": "HSN tax code"},
                    {"name": "default_tax_rate", "type": "DECIMAL(5,2)", "description": "Default GST rate %"},
                    {"name": "description", "type": "TEXT", "description": "Product description"},
                    {"name": "unit_of_measure", "type": "VARCHAR(20)", "description": "Unit (NOS, KG, MTR)"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"}
                ]
            },
            "invoices": {
                "name": "Invoices Table",
                "description": "Invoice header with totals and references",
                "fields": [
                    {"name": "invoice_id", "type": "INTEGER", "description": "Unique invoice identifier"},
                    {"name": "doc_id", "type": "INTEGER", "description": "Source document reference"},
                    {"name": "invoice_num", "type": "VARCHAR(50)", "description": "Invoice number"},
                    {"name": "invoice_date", "type": "DATE", "description": "Invoice date"},
                    {"name": "supplier_company_id", "type": "INTEGER", "description": "Supplier company ID"},
                    {"name": "buyer_company_id", "type": "INTEGER", "description": "Buyer company ID"},
                    {"name": "taxable_value", "type": "DECIMAL(15,2)", "description": "Amount before taxes"},
                    {"name": "total_tax", "type": "DECIMAL(15,2)", "description": "Total tax amount"},
                    {"name": "total_value", "type": "DECIMAL(15,2)", "description": "Final invoice amount"},
                    {"name": "currency", "type": "VARCHAR(3)", "description": "Currency code"},
                    {"name": "status", "type": "VARCHAR(20)", "description": "Processing status"},
                    {"name": "validation", "type": "BOOLEAN", "description": "Arithmetic validation result"},
                    {"name": "duplication", "type": "BOOLEAN", "description": "Duplicate check result"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"}
                ]
            },
            "invoice_item": {
                "name": "Invoice Items Table",
                "description": "Individual line items with tax calculations",
                "fields": [
                    {"name": "item_id", "type": "INTEGER", "description": "Unique item identifier"},
                    {"name": "invoice_id", "type": "INTEGER", "description": "Parent invoice ID"},
                    {"name": "product_id", "type": "INTEGER", "description": "Product reference"},
                    {"name": "hsn_code", "type": "VARCHAR(10)", "description": "HSN tax code"},
                    {"name": "item_description", "type": "VARCHAR(255)", "description": "Item description"},
                    {"name": "quantity", "type": "DECIMAL(10,2)", "description": "Item quantity"},
                    {"name": "unit_price", "type": "DECIMAL(10,2)", "description": "Price per unit"},
                    {"name": "taxable_value", "type": "DECIMAL(15,2)", "description": "Line taxable amount"},
                    {"name": "gst_rate", "type": "DECIMAL(5,2)", "description": "Total GST rate %"},
                    {"name": "gst_amount", "type": "DECIMAL(15,2)", "description": "Total GST amount"},
                    {"name": "sgst_rate", "type": "DECIMAL(5,2)", "description": "State GST rate %"},
                    {"name": "sgst_amount", "type": "DECIMAL(15,2)", "description": "State GST amount"},
                    {"name": "cgst_rate", "type": "DECIMAL(5,2)", "description": "Central GST rate %"},
                    {"name": "cgst_amount", "type": "DECIMAL(15,2)", "description": "Central GST amount"},
                    {"name": "igst_rate", "type": "DECIMAL(5,2)", "description": "Integrated GST rate %"},
                    {"name": "igst_amount", "type": "DECIMAL(15,2)", "description": "Integrated GST amount"},
                    {"name": "total_amount", "type": "DECIMAL(15,2)", "description": "Line total with taxes"},
                    {"name": "created_at", "type": "TIMESTAMP", "description": "Creation timestamp"}
                ]
            }
        }
    
    def get_insertion_report(self, database_ids: Dict[str, Any]) -> Dict[str, Any]:
        """Generate detailed database insertion report"""
        report = {
            "summary": {
                "total_tables_affected": 0,
                "total_records_inserted": 0,
                "processing_timestamp": datetime.now().isoformat()
            },
            "tables": {},
            "relationships": {},
            "business_impact": {}
        }
        
        cursor = self.db.conn.cursor()
        
        # Process each table that had insertions
        for table_name, record_id in database_ids.items():
            if record_id and table_name in self.table_schemas:
                table_data = self._get_table_insertion_details(cursor, table_name, record_id)
                if table_data:
                    report["tables"][table_name] = table_data
                    report["summary"]["total_tables_affected"] += 1
                    report["summary"]["total_records_inserted"] += len(table_data["records"])
        
        # Add relationship information
        report["relationships"] = self._get_relationship_info(database_ids)
        
        # Add business impact
        report["business_impact"] = self._get_business_impact(database_ids)
        
        return report
    
    def _get_table_insertion_details(self, cursor: sqlite3.Cursor, table_name: str, record_id: Any) -> Dict[str, Any]:
        """Get detailed information about insertions in a specific table"""
        schema = self.table_schemas.get(table_name)
        if not schema:
            return None
        
        # Handle multiple IDs (for invoice_item table)
        if isinstance(record_id, list):
            record_ids = record_id
        else:
            record_ids = [record_id]
        
        # Get primary key column name
        pk_column = f"{table_name[:-1] if table_name.endswith('s') else table_name}_id"
        if table_name == "invoice_item":
            pk_column = "item_id"
        elif table_name == "gst_companies":
            pk_column = "gst_id"
        
        records = []
        for rid in record_ids:
            cursor.execute(f"SELECT * FROM {table_name} WHERE {pk_column} = ?", (rid,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                record_data = dict(zip(columns, row))
                
                # Format the record with field descriptions
                formatted_record = {
                    "record_id": rid,
                    "fields": {}
                }
                
                for field in schema["fields"]:
                    field_name = field["name"]
                    if field_name in record_data:
                        value = record_data[field_name]
                        formatted_record["fields"][field_name] = {
                            "value": value,
                            "type": field["type"],
                            "description": field["description"],
                            "formatted_value": self._format_field_value(field_name, value)
                        }
                
                records.append(formatted_record)
        
        return {
            "table_info": {
                "name": schema["name"],
                "description": schema["description"],
                "total_fields": len(schema["fields"])
            },
            "records": records,
            "insertion_summary": {
                "records_inserted": len(records),
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _format_field_value(self, field_name: str, value: Any) -> str:
        """Format field values for better display"""
        if value is None:
            return "NULL"
        
        if field_name.endswith('_at') and isinstance(value, str):
            try:
                # Format timestamp
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                return str(value)
        
        if field_name in ['taxable_value', 'total_tax', 'total_value', 'gst_amount', 
                         'sgst_amount', 'cgst_amount', 'igst_amount', 'total_amount', 
                         'unit_price', 'analysis_confidence']:
            if isinstance(value, (int, float)):
                if field_name == 'analysis_confidence':
                    return f"{value}%"
                else:
                    return f"₹{value:,.2f}"
        
        if field_name in ['gst_rate', 'sgst_rate', 'cgst_rate', 'igst_rate', 'default_tax_rate']:
            if isinstance(value, (int, float)):
                return f"{value}%"
        
        if field_name == 'file_size_bytes' and isinstance(value, int):
            if value > 1024 * 1024:
                return f"{value / (1024 * 1024):.1f} MB"
            elif value > 1024:
                return f"{value / 1024:.1f} KB"
            else:
                return f"{value} bytes"
        
        return str(value)
    
    def _get_relationship_info(self, database_ids: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about table relationships"""
        relationships = {}
        
        # Document to Invoice relationship
        if "document_id" in database_ids and "invoice_id" in database_ids:
            relationships["document_to_invoice"] = {
                "type": "One-to-One",
                "description": f"Document ID {database_ids['document_id']} → Invoice ID {database_ids['invoice_id']}",
                "business_rule": "Each document can generate one primary invoice"
            }
        
        # Company relationships
        if "supplier_company_id" in database_ids:
            relationships["supplier_company"] = {
                "type": "Many-to-One",
                "description": f"Invoice references Supplier Company ID {database_ids['supplier_company_id']}",
                "business_rule": "Multiple invoices can come from same supplier"
            }
        
        if "buyer_company_id" in database_ids:
            relationships["buyer_company"] = {
                "type": "Many-to-One", 
                "description": f"Invoice references Buyer Company ID {database_ids['buyer_company_id']}",
                "business_rule": "Multiple invoices can be sent to same buyer"
            }
        
        # Invoice to Items relationship
        if "invoice_id" in database_ids and "invoice_item_ids" in database_ids:
            item_count = len(database_ids["invoice_item_ids"]) if isinstance(database_ids["invoice_item_ids"], list) else 1
            relationships["invoice_to_items"] = {
                "type": "One-to-Many",
                "description": f"Invoice ID {database_ids['invoice_id']} → {item_count} Line Items",
                "business_rule": "Each invoice can have multiple line items"
            }
        
        # Product relationships
        if "product_ids" in database_ids:
            product_count = len(database_ids["product_ids"]) if isinstance(database_ids["product_ids"], list) else 1
            relationships["products_referenced"] = {
                "type": "Reference",
                "description": f"Line items reference {product_count} products in catalog", 
                "business_rule": "Products are maintained in master catalog for consistency"
            }
        
        return relationships
    
    def _get_business_impact(self, database_ids: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate business impact of the insertions"""
        cursor = self.db.conn.cursor()
        impact = {
            "data_quality": {},
            "compliance": {},
            "operational": {}
        }
        
        # Data Quality Impact
        if "invoice_id" in database_ids:
            # Check validation status
            cursor.execute("SELECT validation, duplication FROM invoices WHERE invoice_id = ?", 
                         (database_ids["invoice_id"],))
            result = cursor.fetchone()
            if result:
                validation, duplication = result
                impact["data_quality"]["arithmetic_validation"] = {
                    "status": "PASSED" if validation else "FAILED",
                    "description": "Invoice totals match line item calculations"
                }
                impact["data_quality"]["duplication_check"] = {
                    "status": "DUPLICATE DETECTED" if duplication else "UNIQUE",
                    "description": "Invoice number uniqueness verified"
                }
        
        # Compliance Impact
        if "supplier_company_id" in database_ids:
            cursor.execute("SELECT gstin FROM companies WHERE company_id = ?", 
                         (database_ids["supplier_company_id"],))
            result = cursor.fetchone()
            if result and result[0]:
                impact["compliance"]["gst_compliance"] = {
                    "status": "COMPLIANT",
                    "description": f"Supplier has valid GSTIN: {result[0]}"
                }
            else:
                impact["compliance"]["gst_compliance"] = {
                    "status": "NON-COMPLIANT", 
                    "description": "Supplier GSTIN missing or invalid"
                }
        
        # Operational Impact
        cursor.execute("SELECT COUNT(*) FROM invoices")
        total_invoices = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        total_products = cursor.fetchone()[0]
        
        impact["operational"]["database_growth"] = {
            "total_invoices": total_invoices,
            "total_companies": total_companies,  
            "total_products": total_products,
            "description": "Current database size after processing"
        }
        
        return impact

def main():
    """Generate database insertion report from command line arguments"""
    import sys
    
    if len(sys.argv) > 1:
        # Parse database IDs from command line argument
        try:
            database_ids = json.loads(sys.argv[1])
            reporter = DatabaseReporter()
            report = reporter.get_insertion_report(database_ids)
            print(json.dumps(report, indent=2, default=str))
        except Exception as e:
            print(json.dumps({
                "error": f"Failed to generate database report: {str(e)}",
                "input_received": sys.argv[1] if len(sys.argv) > 1 else None
            }, indent=2))
    else:
        # Test mode with sample data
        reporter = DatabaseReporter()
        
        # Sample database IDs (as would be returned from processing)
        sample_ids = {
            "document_id": 1,
            "invoice_id": 1,
            "supplier_company_id": 1,
            "buyer_company_id": 2,
            "invoice_item_ids": [1, 2],
            "product_ids": [1, 2]
        }
        
        report = reporter.get_insertion_report(sample_ids)
        print(json.dumps(report, indent=2, default=str))

if __name__ == "__main__":
    main()