#!/usr/bin/env python3
"""
LangChain Schema Configuration for Invoice Management Chatbot

This module provides LangChain/LangGraph compatible schema definitions
for the financial database to enable accurate AI agent interactions.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import Tool
from langchain.schema import BaseRetriever
from pydantic import BaseModel, Field
import sqlite3
import json

class DatabaseQuery(BaseModel):
    """Structured database query for financial data"""
    query_type: str = Field(description="Type of query: search, aggregate, validate, or report")
    table_name: str = Field(description="Primary table to query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    join_tables: List[str] = Field(default_factory=list, description="Tables to join")
    fields: List[str] = Field(default_factory=list, description="Specific fields to return")
    limit: Optional[int] = Field(default=None, description="Maximum results to return")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")

class FinancialSearchResult(BaseModel):
    """Structured result for financial data searches"""
    result_type: str = Field(description="Type of result: invoice, company, product, or summary")
    data: List[Dict[str, Any]] = Field(description="Query result data")
    total_count: int = Field(description="Total matching records")
    confidence: float = Field(description="Confidence in result accuracy")
    source_tables: List[str] = Field(description="Tables used in query")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

# Database schema for LangChain tools
LANGCHAIN_SCHEMA = {
    "invoice_search": {
        "description": "Search invoices by various criteria including supplier, buyer, date range, amount, status",
        "parameters": {
            "supplier_name": {"type": "string", "description": "Supplier company name (partial match supported)"},
            "buyer_name": {"type": "string", "description": "Buyer company name (partial match supported)"},
            "gstin": {"type": "string", "description": "GST identification number (exact match)"},
            "invoice_number": {"type": "string", "description": "Invoice number (partial match supported)"},
            "date_from": {"type": "string", "format": "date", "description": "Start date (YYYY-MM-DD)"},
            "date_to": {"type": "string", "format": "date", "description": "End date (YYYY-MM-DD)"},
            "amount_min": {"type": "number", "description": "Minimum invoice amount"},
            "amount_max": {"type": "number", "description": "Maximum invoice amount"},
            "status": {"type": "string", "enum": ["PENDING", "PROCESSED", "PAID", "CANCELLED"], "description": "Invoice status"},
            "validation_status": {"type": "boolean", "description": "Arithmetic validation result"},
            "duplication_flag": {"type": "boolean", "description": "Duplication check result"}
        }
    },
    
    "company_lookup": {
        "description": "Look up company information including GST validation and business details",
        "parameters": {
            "company_name": {"type": "string", "description": "Company name (partial match supported)"},
            "gstin": {"type": "string", "description": "GST identification number"},
            "state": {"type": "string", "description": "State where company is registered"},
            "status": {"type": "string", "enum": ["Active", "Cancelled", "Suspended"], "description": "GST status"},
            "include_gst_details": {"type": "boolean", "default": True, "description": "Include detailed GST information"}
        }
    },
    
    "product_search": {
        "description": "Search products by name, HSN code, or tax rate",
        "parameters": {
            "product_name": {"type": "string", "description": "Product name (partial match supported)"},
            "hsn_code": {"type": "string", "description": "HSN code (exact or partial match)"},
            "tax_rate": {"type": "number", "description": "GST tax rate percentage"},
            "unit_of_measure": {"type": "string", "description": "Unit of measurement"}
        }
    },
    
    "financial_analysis": {
        "description": "Perform financial analysis and generate reports",
        "parameters": {
            "analysis_type": {
                "type": "string", 
                "enum": ["tax_summary", "supplier_analysis", "monthly_trends", "compliance_check"],
                "description": "Type of financial analysis"
            },
            "date_from": {"type": "string", "format": "date", "description": "Analysis start date"},
            "date_to": {"type": "string", "format": "date", "description": "Analysis end date"},
            "group_by": {
                "type": "string", 
                "enum": ["supplier", "month", "product", "tax_rate"],
                "description": "How to group the analysis results"
            }
        }
    },
    
    "gst_validation": {
        "description": "Validate GST numbers and retrieve taxpayer information",
        "parameters": {
            "gstin": {"type": "string", "description": "15-character GST identification number"},
            "company_name": {"type": "string", "description": "Company name for cross-validation"},
            "force_refresh": {"type": "boolean", "default": False, "description": "Force fresh API lookup"}
        }
    },
    
    "invoice_validation": {
        "description": "Validate invoice data for arithmetic accuracy and compliance",
        "parameters": {
            "invoice_id": {"type": "integer", "description": "Invoice ID to validate"},
            "validation_type": {
                "type": "string",
                "enum": ["arithmetic", "tax_compliance", "duplication", "full"],
                "description": "Type of validation to perform"
            }
        }
    },
    
    "payment_tracking": {
        "description": "Track payments against invoices and analyze payment patterns",
        "parameters": {
            "invoice_id": {"type": "integer", "description": "Invoice ID to check payments"},
            "payment_status": {
                "type": "string",
                "enum": ["PENDING", "PROCESSED", "FAILED"],
                "description": "Payment status filter"
            },
            "date_from": {"type": "string", "format": "date", "description": "Payment date range start"},
            "date_to": {"type": "string", "format": "date", "description": "Payment date range end"}
        }
    }
}

# Natural language query patterns for understanding user intent
NL_QUERY_PATTERNS = {
    "invoice_search": [
        "find invoices", "search invoices", "show me invoices", "list invoices",
        "invoices from", "invoices by", "invoices between", "invoices above",
        "invoices below", "pending invoices", "paid invoices"
    ],
    
    "company_lookup": [
        "company details", "company information", "find company", "lookup company",
        "GST details", "supplier info", "buyer info", "company profile"
    ],
    
    "financial_analysis": [
        "total amount", "sum of", "average", "analysis", "report", "summary",
        "trends", "monthly", "quarterly", "tax analysis", "compliance report"
    ],
    
    "gst_validation": [
        "validate GST", "check GST", "verify GST", "GST status", "taxpayer details",
        "is GST valid", "GST information"
    ],
    
    "invoice_validation": [
        "validate invoice", "check invoice", "invoice errors", "arithmetic check",
        "tax calculation", "duplicate invoice"
    ]
}

# Financial domain-specific terminology for better understanding
FINANCIAL_TERMINOLOGY = {
    "tax_terms": {
        "GST": "Goods and Services Tax",
        "CGST": "Central Goods and Services Tax",
        "SGST": "State Goods and Services Tax", 
        "IGST": "Integrated Goods and Services Tax",
        "HSN": "Harmonized System of Nomenclature",
        "GSTIN": "GST Identification Number",
        "PAN": "Permanent Account Number"
    },
    
    "transaction_terms": {
        "taxable_value": "Amount before adding taxes",
        "total_value": "Final amount including all taxes",
        "unit_price": "Price per individual item",
        "invoice_number": "Unique identifier for the invoice",
        "invoice_date": "Date when invoice was issued"
    },
    
    "compliance_terms": {
        "intra_state": "Transaction within the same state (CGST + SGST)",
        "inter_state": "Transaction between different states (IGST)",
        "composition_scheme": "Simplified GST scheme for small businesses",
        "reverse_charge": "Tax liability on recipient instead of supplier"
    }
}

# Data validation rules for financial accuracy
VALIDATION_RULES = {
    "gstin_format": {
        "pattern": r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z]{1}[0-9A-Z]{1}$",
        "description": "15-character alphanumeric GST identification number"
    },
    
    "pan_format": {
        "pattern": r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
        "description": "10-character PAN number embedded in GSTIN"
    },
    
    "tax_rates": {
        "valid_rates": [0, 3, 5, 12, 18, 28],
        "description": "Valid GST tax rates in India"
    },
    
    "amount_precision": {
        "decimal_places": 2,
        "description": "Financial amounts should have maximum 2 decimal places"
    }
}

# Query safety rules to prevent hallucination with financial data
SAFETY_RULES = {
    "data_sources": [
        "NEVER generate mock, sample, or estimated financial data",
        "ONLY use actual database query results - no exceptions",
        "If database returns empty results, state 'No data found' explicitly",
        "Always query actual database, never generate placeholder financial data",
        "Clearly indicate when data is calculated vs retrieved from database",
        "Provide exact source table and column names for all financial figures",
        "Include confidence levels based on data completeness and accuracy"
    ],
    
    "calculation_accuracy": [
        "Verify all arithmetic calculations against source database values",
        "Round currency amounts to exactly 2 decimal places as stored in database",
        "Check tax calculations match actual GST rules and database records",
        "Flag any discrepancies between calculated and stored values",
        "Never estimate or fill in missing financial data with assumptions",
        "Show exact calculation formulas when computing derived values"
    ],
    
    "compliance_checks": [
        "Validate GSTIN format before using in queries and responses",
        "Ensure tax rates match actual HSN code requirements from database",
        "Check inter-state vs intra-state tax rules against actual invoice data",
        "Verify company status from actual GST database records only",
        "Never assume or generate compliance information not in database"
    ],
    
    "user_communication": [
        "Always state actual data source and query timestamp",
        "Explain any assumptions or limitations in available data",
        "Recommend verification for critical financial decisions",
        "Provide raw database data when requested",
        "Never use phrases like 'for example' or 'typically' with financial figures",
        "Clearly distinguish between actual database values and calculated results"
    ]
}

# Memory structure for conversation context
CONVERSATION_MEMORY_SCHEMA = {
    "session_info": {
        "session_id": "string",
        "user_id": "string", 
        "start_time": "timestamp",
        "last_activity": "timestamp"
    },
    
    "query_history": {
        "queries": "list of previous queries",
        "results": "list of query results",
        "feedback": "user feedback on results"
    },
    
    "user_preferences": {
        "default_date_range": "preferred analysis period",
        "favorite_companies": "frequently searched companies",
        "preferred_metrics": "commonly requested analyses",
        "notification_settings": "alert preferences"
    },
    
    "context_state": {
        "current_invoice": "currently discussed invoice",
        "current_company": "currently discussed company",
        "current_analysis": "ongoing analysis context",
        "pending_actions": "user requested follow-ups"
    }
}

def get_schema_for_tool(tool_name: str) -> Dict[str, Any]:
    """Get schema definition for a specific tool"""
    return LANGCHAIN_SCHEMA.get(tool_name, {})

def get_query_patterns(intent: str) -> List[str]:
    """Get natural language patterns for query intent"""
    return NL_QUERY_PATTERNS.get(intent, [])

def validate_financial_data(data_type: str, value: Any) -> bool:
    """Validate financial data according to rules"""
    rules = VALIDATION_RULES.get(data_type)
    if not rules:
        return True
    
    if data_type == "gstin_format":
        import re
        return bool(re.match(rules["pattern"], str(value)))
    elif data_type == "tax_rates":
        return value in rules["valid_rates"]
    
    return True