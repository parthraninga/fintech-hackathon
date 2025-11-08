#!/usr/bin/env python3
"""
Database Schema for LangChain/LangGraph Integration

This file defines the complete database schema for the Invoice Management System
and GST Validation database. It provides structured information for AI agents
to understand and interact with the financial data.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class TableType(Enum):
    CORE = "core"
    REFERENCE = "reference"
    TRANSACTION = "transaction"
    AUDIT = "audit"

@dataclass
class ColumnInfo:
    """Information about a database column"""
    name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_table: Optional[str] = None
    is_nullable: bool = True
    default_value: Optional[str] = None
    description: str = ""
    constraints: List[str] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []

@dataclass
class TableSchema:
    """Complete schema information for a database table"""
    name: str
    description: str
    table_type: TableType
    columns: List[ColumnInfo]
    indexes: List[str] = None
    relationships: List[str] = None
    business_rules: List[str] = None
    
    def __post_init__(self):
        if self.indexes is None:
            self.indexes = []
        if self.relationships is None:
            self.relationships = []
        if self.business_rules is None:
            self.business_rules = []

# Core Financial Tables
DOCUMENTS_TABLE = TableSchema(
    name="documents",
    description="Document metadata for all uploaded financial documents (invoices, receipts, etc.)",
    table_type=TableType.CORE,
    columns=[
        ColumnInfo("doc_id", "INTEGER", is_primary_key=True, description="Unique document identifier"),
        ColumnInfo("doc_type", "VARCHAR(50)", is_nullable=False, description="Type of document (INVOICE, RECEIPT, etc.)"),
        ColumnInfo("created_at", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Document upload timestamp"),
        ColumnInfo("filename", "VARCHAR(255)", description="Original filename of uploaded document"),
        ColumnInfo("file_size_bytes", "INTEGER", description="File size in bytes"),
        ColumnInfo("analysis_confidence", "DECIMAL(5,2)", description="AI analysis confidence score (0-100)"),
        ColumnInfo("raw_data", "TEXT", description="Original Textract JSON data")
    ],
    indexes=["idx_documents_type"],
    business_rules=[
        "Document types must be from predefined list: INVOICE, RECEIPT, PAYMENT_ADVICE",
        "Analysis confidence should be between 0 and 100",
        "Raw data contains original OCR output for audit purposes"
    ]
)

COMPANIES_TABLE = TableSchema(
    name="companies",
    description="Company master data including suppliers and buyers with GST information",
    table_type=TableType.REFERENCE,
    columns=[
        ColumnInfo("company_id", "INTEGER", is_primary_key=True, description="Unique company identifier"),
        ColumnInfo("legal_name", "VARCHAR(255)", is_nullable=False, description="Official registered company name"),
        ColumnInfo("gstin", "VARCHAR(15)", constraints=["UNIQUE"], description="GST Identification Number (15 chars)"),
        ColumnInfo("city", "VARCHAR(100)", description="Company registered city"),
        ColumnInfo("state", "VARCHAR(50)", description="Company registered state"),
        ColumnInfo("address", "TEXT", description="Complete registered address"),
        ColumnInfo("phone", "VARCHAR(20)", description="Primary contact phone number"),
        ColumnInfo("email", "VARCHAR(100)", description="Primary contact email"),
        ColumnInfo("created_at", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Record creation timestamp")
    ],
    indexes=["idx_companies_gstin"],
    relationships=[
        "One-to-many with invoices (as supplier)",
        "One-to-many with invoices (as buyer)"
    ],
    business_rules=[
        "GSTIN must be 15 characters if provided",
        "GSTIN format: 2-digit state code + 10-digit PAN + 1-digit entity code + 1-digit check digit",
        "Legal name is mandatory for all companies"
    ]
)

GST_COMPANIES_TABLE = TableSchema(
    name="gst_companies",
    description="Validated GST company information from government APIs with detailed taxpayer data",
    table_type=TableType.REFERENCE,
    columns=[
        ColumnInfo("gst_id", "INTEGER", is_primary_key=True, description="Unique GST record identifier"),
        ColumnInfo("gstin", "VARCHAR(15)", is_nullable=False, constraints=["UNIQUE"], description="GST Identification Number"),
        ColumnInfo("legal_name", "VARCHAR(255)", description="Official legal name from GST records"),
        ColumnInfo("trade_name", "VARCHAR(255)", description="Trade/business name"),
        ColumnInfo("pan", "VARCHAR(10)", description="Permanent Account Number"),
        ColumnInfo("registration_date", "VARCHAR(20)", description="GST registration date"),
        ColumnInfo("constitution", "VARCHAR(100)", description="Business constitution (Partnership, Private Limited, etc.)"),
        ColumnInfo("taxpayer_type", "VARCHAR(50)", description="Type of taxpayer (Regular, Composition, etc.)"),
        ColumnInfo("status", "VARCHAR(20)", description="Current GST status (Active, Cancelled, Suspended)"),
        ColumnInfo("state", "VARCHAR(50)", description="Registered state"),
        ColumnInfo("pin_code", "VARCHAR(10)", description="PIN code of registered address"),
        ColumnInfo("cancellation_date", "VARCHAR(20)", description="GST cancellation date if applicable"),
        ColumnInfo("state_jurisdiction", "VARCHAR(255)", description="State tax jurisdiction"),
        ColumnInfo("centre_jurisdiction", "VARCHAR(255)", description="Central tax jurisdiction"),
        ColumnInfo("nature_of_business", "TEXT", description="Description of business activities"),
        ColumnInfo("api_source", "VARCHAR(50)", description="Source API used for validation"),
        ColumnInfo("last_verified", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Last verification timestamp"),
        ColumnInfo("created_at", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Record creation timestamp")
    ],
    indexes=["idx_gst_companies_gstin", "idx_gst_companies_status"],
    business_rules=[
        "GSTIN must be validated against government database",
        "Status must be one of: Active, Cancelled, Suspended",
        "PAN is embedded in GSTIN (characters 3-12)",
        "Records are cached for performance and updated periodically"
    ]
)

PRODUCTS_TABLE = TableSchema(
    name="products",
    description="Product master catalog with HSN codes and tax information",
    table_type=TableType.REFERENCE,
    columns=[
        ColumnInfo("product_id", "INTEGER", is_primary_key=True, description="Unique product identifier"),
        ColumnInfo("canonical_name", "VARCHAR(255)", is_nullable=False, description="Standardized product name"),
        ColumnInfo("hsn_code", "VARCHAR(10)", is_nullable=False, description="Harmonized System of Nomenclature code"),
        ColumnInfo("default_tax_rate", "DECIMAL(5,2)", default_value="18.00", description="Default GST rate percentage"),
        ColumnInfo("description", "TEXT", description="Detailed product description"),
        ColumnInfo("unit_of_measure", "VARCHAR(20)", default_value="'NOS'", description="Unit of measurement (NOS, KG, METER, etc.)"),
        ColumnInfo("created_at", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Record creation timestamp")
    ],
    indexes=["idx_products_hsn"],
    business_rules=[
        "HSN code determines tax rate and compliance requirements",
        "Default tax rates: 0%, 5%, 12%, 18%, 28%",
        "Unit of measure must be from standard list"
    ]
)

INVOICES_TABLE = TableSchema(
    name="invoices",
    description="Invoice header information with supplier, buyer, and totals",
    table_type=TableType.TRANSACTION,
    columns=[
        ColumnInfo("invoice_id", "INTEGER", is_primary_key=True, description="Unique invoice identifier"),
        ColumnInfo("doc_id", "INTEGER", is_foreign_key=True, foreign_table="documents", is_nullable=False, description="Reference to source document"),
        ColumnInfo("invoice_num", "VARCHAR(50)", is_nullable=False, description="Invoice number from supplier"),
        ColumnInfo("invoice_date", "DATE", description="Invoice issue date"),
        ColumnInfo("supplier_company_id", "INTEGER", is_foreign_key=True, foreign_table="companies", description="Supplier company reference"),
        ColumnInfo("buyer_company_id", "INTEGER", is_foreign_key=True, foreign_table="companies", description="Buyer company reference"),
        ColumnInfo("taxable_value", "DECIMAL(15,2)", description="Total taxable amount before taxes"),
        ColumnInfo("total_tax", "DECIMAL(15,2)", description="Total tax amount (CGST + SGST + IGST)"),
        ColumnInfo("total_value", "DECIMAL(15,2)", description="Final invoice amount including taxes"),
        ColumnInfo("currency", "VARCHAR(3)", default_value="'INR'", description="Currency code (INR, USD, etc.)"),
        ColumnInfo("status", "VARCHAR(20)", default_value="'PENDING'", description="Processing status"),
        ColumnInfo("validation", "BOOLEAN", default_value="0", description="Arithmetic validation result"),
        ColumnInfo("duplication", "BOOLEAN", default_value="0", description="Duplication check result"),
        ColumnInfo("created_at", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Record creation timestamp")
    ],
    indexes=["idx_invoices_num", "idx_invoices_date"],
    relationships=[
        "Many-to-one with documents",
        "Many-to-one with companies (supplier)",
        "Many-to-one with companies (buyer)",
        "One-to-many with invoice_item"
    ],
    business_rules=[
        "Invoice number must be unique per supplier",
        "Total value = Taxable value + Total tax",
        "Validation checks arithmetic accuracy",
        "Duplication flag indicates potential duplicate invoices"
    ]
)

INVOICE_ITEMS_TABLE = TableSchema(
    name="invoice_item",
    description="Individual line items within invoices with product details and tax calculations",
    table_type=TableType.TRANSACTION,
    columns=[
        ColumnInfo("item_id", "INTEGER", is_primary_key=True, description="Unique item identifier"),
        ColumnInfo("invoice_id", "INTEGER", is_foreign_key=True, foreign_table="invoices", is_nullable=False, description="Parent invoice reference"),
        ColumnInfo("product_id", "INTEGER", is_foreign_key=True, foreign_table="products", description="Product catalog reference"),
        ColumnInfo("hsn_code", "VARCHAR(10)", description="HSN code for this item"),
        ColumnInfo("item_description", "VARCHAR(255)", description="Item description from invoice"),
        ColumnInfo("quantity", "DECIMAL(10,2)", description="Quantity of items"),
        ColumnInfo("unit_price", "DECIMAL(10,2)", description="Price per unit"),
        ColumnInfo("taxable_value", "DECIMAL(15,2)", description="Line item taxable amount"),
        ColumnInfo("gst_rate", "DECIMAL(5,2)", description="Total GST rate percentage"),
        ColumnInfo("gst_amount", "DECIMAL(15,2)", description="Total GST amount"),
        ColumnInfo("sgst_rate", "DECIMAL(5,2)", description="State GST rate percentage"),
        ColumnInfo("sgst_amount", "DECIMAL(15,2)", description="State GST amount"),
        ColumnInfo("igst_rate", "DECIMAL(5,2)", description="Integrated GST rate percentage"),
        ColumnInfo("igst_amount", "DECIMAL(15,2)", description="Integrated GST amount"),
        ColumnInfo("cgst_rate", "DECIMAL(5,2)", description="Central GST rate percentage"),
        ColumnInfo("cgst_amount", "DECIMAL(15,2)", description="Central GST amount"),
        ColumnInfo("total_amount", "DECIMAL(15,2)", description="Line total including taxes"),
        ColumnInfo("created_at", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Record creation timestamp")
    ],
    indexes=["idx_invoice_items_invoice"],
    business_rules=[
        "CGST + SGST rates should equal GST rate for intra-state transactions",
        "IGST rate should equal GST rate for inter-state transactions",
        "Total amount = Taxable value + GST amount",
        "Taxable value = Quantity × Unit price"
    ]
)

PAYMENTS_TABLE = TableSchema(
    name="payment",
    description="Payment records linked to invoices and documents",
    table_type=TableType.TRANSACTION,
    columns=[
        ColumnInfo("payment_id", "INTEGER", is_primary_key=True, description="Unique payment identifier"),
        ColumnInfo("doc_id", "INTEGER", is_foreign_key=True, foreign_table="documents", description="Source document reference"),
        ColumnInfo("invoice_id", "INTEGER", is_foreign_key=True, foreign_table="invoices", description="Related invoice reference"),
        ColumnInfo("payment_date", "DATE", description="Date of payment"),
        ColumnInfo("payment_method", "VARCHAR(50)", description="Payment method (NEFT, RTGS, UPI, etc.)"),
        ColumnInfo("amount", "DECIMAL(15,2)", description="Payment amount"),
        ColumnInfo("transaction_ref", "VARCHAR(100)", description="Bank transaction reference"),
        ColumnInfo("bank_details", "VARCHAR(255)", description="Bank account details"),
        ColumnInfo("status", "VARCHAR(20)", default_value="'PENDING'", description="Payment status"),
        ColumnInfo("created_at", "TIMESTAMP", default_value="CURRENT_TIMESTAMP", description="Record creation timestamp")
    ],
    indexes=["idx_payments_invoice"],
    business_rules=[
        "Payment amount should not exceed invoice total",
        "Multiple partial payments allowed per invoice",
        "Transaction reference must be unique per payment method"
    ]
)

# Complete database schema
DATABASE_SCHEMA = {
    "documents": DOCUMENTS_TABLE,
    "companies": COMPANIES_TABLE,
    "gst_companies": GST_COMPANIES_TABLE,
    "products": PRODUCTS_TABLE,
    "invoices": INVOICES_TABLE,
    "invoice_item": INVOICE_ITEMS_TABLE,
    "payment": PAYMENTS_TABLE
}

# Business relationships and constraints
BUSINESS_RELATIONSHIPS = {
    "invoice_lifecycle": [
        "Document uploaded → Invoice extracted → Items parsed → Companies validated → Payment processed"
    ],
    "gst_validation": [
        "Company GSTIN → GST API lookup → Validation result → Database cache"
    ],
    "tax_calculations": [
        "HSN code → Tax rate → CGST/SGST (intra-state) or IGST (inter-state)"
    ]
}

# Key business rules for AI agents
BUSINESS_RULES = {
    "data_integrity": [
        "All financial amounts must be non-negative",
        "Invoice totals must equal sum of line items",
        "Tax calculations must be accurate within 0.01 precision",
        "GSTIN format must be validated before storing"
    ],
    "compliance": [
        "GST rates must match HSN code requirements",
        "Inter-state transactions use IGST, intra-state use CGST+SGST",
        "Invoice numbers must be unique per supplier",
        "All companies must have valid GSTIN for B2B transactions"
    ],
    "audit_trail": [
        "All changes must be timestamped",
        "Original document data preserved in raw_data",
        "Validation and duplication flags maintained",
        "API sources tracked for GST data"
    ]
}

def get_table_schema(table_name: str) -> Optional[TableSchema]:
    """Get schema for a specific table"""
    return DATABASE_SCHEMA.get(table_name)

def get_all_tables() -> List[str]:
    """Get list of all table names"""
    return list(DATABASE_SCHEMA.keys())

def get_financial_tables() -> List[str]:
    """Get tables containing financial data"""
    return ["invoices", "invoice_item", "payment"]

def get_reference_tables() -> List[str]:
    """Get reference/master data tables"""
    return ["companies", "gst_companies", "products"]

def get_table_relationships() -> Dict[str, List[str]]:
    """Get table relationships for query planning"""
    return {
        "documents": ["invoices", "payment"],
        "companies": ["invoices (supplier)", "invoices (buyer)"],
        "gst_companies": ["companies (gstin lookup)"],
        "products": ["invoice_item"],
        "invoices": ["invoice_item", "payment"],
        "invoice_item": [],
        "payment": []
    }