#!/usr/bin/env python3
"""
Enhanced Invoice AI Agent with Tesseract OCR + Textract + LangGraph

This intelligent agent combines:
1. Tesseract OCR for raw text extraction from PDFs
2. Textract JSON analysis for structured data
3. AI processing using both text sources for maximum accuracy
4. Real-time database storage with no mock data
5. Memory system for continuous learning

Features:
- Dual-source text extraction (OCR + Textract)
- AI-powered entity extraction using combined data
- Clean database operations (no mock data)
- Enhanced accuracy through multiple text sources
- Comprehensive error handling and validation
"""

import json
import sqlite3
from datetime import datetime, date
from typing import Dict, List, Any, Optional, TypedDict, Tuple
import os
import sys
from dataclasses import dataclass
import re
from decimal import Decimal

# OCR and PDF processing imports
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import tempfile

# LangChain imports
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

# Local imports
from invoice_database import InvoiceDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ExtractedInvoiceData:
    """Structured data class for extracted invoice information"""
    # Document info
    document_type: str
    filename: str
    confidence_score: float
    
    # Company info
    supplier_name: Optional[str] = None
    supplier_gstin: Optional[str] = None
    supplier_address: Optional[str] = None
    buyer_name: Optional[str] = None
    buyer_gstin: Optional[str] = None
    
    # Invoice details
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    taxable_value: Optional[float] = None
    total_tax: Optional[float] = None
    total_amount: Optional[float] = None
    
    # Line items
    line_items: List[Dict] = None
    
    # Payment info
    payment_terms: Optional[str] = None
    
    # Raw data
    raw_form_fields: List[Dict] = None
    raw_tables: List[Dict] = None
    ocr_text: Optional[str] = None

class AgentState(TypedDict):
    """State management for the enhanced AI agent"""
    pdf_path: str
    textract_json: Dict
    ocr_text: str
    extracted_data: Optional[ExtractedInvoiceData]
    database_ids: Dict[str, int]
    messages: List
    errors: List[str]
    processing_step: str
    memory_updates: List[Dict]

class EnhancedInvoiceAIAgent:
    def __init__(self, google_api_key: str = None, db_path: str = "invoice_management.db"):
        """Initialize the enhanced AI agent with OCR and database connections"""
        
        # Set up Google Gemini AI
        self.api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            print("⚠️  Google API key not found. Please set GOOGLE_API_KEY environment variable.")
            print("For now, using rule-based extraction...")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=self.api_key,
            temperature=0.1
        ) if self.api_key else None
        
        # Database connection (create fresh database without sample data)
        self.db = InvoiceDatabase(db_path)
        self._clear_sample_data()
        
        # Memory for learning
        self.memory = MemorySaver()
        
        # Initialize processing graph
        self.graph = self._build_processing_graph()
        
        print(f"✅ Enhanced Invoice AI Agent initialized")
        print(f"   Database: {db_path} (clean, no mock data)")
        print(f"   OCR: Tesseract {self._get_tesseract_version()}")
        print(f"   LLM: {'Google Gemini 1.5 Flash' if self.llm else 'Rule-based processing'}")
    
    def _clear_sample_data(self):
        """Remove all sample/mock data from database"""
        cursor = self.db.conn.cursor()
        
        try:
            # Delete all existing data
            cursor.execute("DELETE FROM payment")
            cursor.execute("DELETE FROM invoice_item") 
            cursor.execute("DELETE FROM invoices")
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM products")
            cursor.execute("DELETE FROM companies")
            
            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence")
            
            self.db.conn.commit()
            print("🧹 Cleared all sample data from database")
            
        except Exception as e:
            print(f"⚠️  Error clearing sample data: {e}")
    
    def _get_tesseract_version(self) -> str:
        """Get Tesseract version"""
        try:
            return pytesseract.get_tesseract_version()
        except:
            return "Unknown"
    
    def _build_processing_graph(self) -> StateGraph:
        """Build the enhanced LangGraph processing workflow"""
        
        # Define the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each processing step
        workflow.add_node("extract_ocr", self._extract_ocr_node)
        workflow.add_node("parse_textract", self._parse_textract_node)
        workflow.add_node("ai_extraction", self._ai_extraction_node)
        workflow.add_node("validate_data", self._validate_data_node)
        workflow.add_node("store_database", self._store_database_node)
        workflow.add_node("update_memory", self._update_memory_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define the workflow edges
        workflow.add_edge(START, "extract_ocr")
        workflow.add_edge("extract_ocr", "parse_textract")
        workflow.add_edge("parse_textract", "ai_extraction")
        workflow.add_edge("ai_extraction", "validate_data")
        workflow.add_edge("validate_data", "store_database")
        workflow.add_edge("store_database", "update_memory")
        workflow.add_edge("update_memory", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile the graph
        return workflow.compile(checkpointer=self.memory)
    
    def _extract_ocr_node(self, state: AgentState) -> AgentState:
        """Extract text using Tesseract OCR"""
        print("🔍 Step 1: Extracting text with Tesseract OCR...")
        
        try:
            pdf_path = state["pdf_path"]
            if not os.path.exists(pdf_path):
                state["errors"].append(f"PDF file not found: {pdf_path}")
                state["ocr_text"] = ""
                return state
            
            # Convert PDF to images
            print("   Converting PDF to images...")
            pages = convert_from_path(pdf_path, dpi=300)
            
            # Extract text from each page
            ocr_text_parts = []
            for i, page in enumerate(pages):
                print(f"   Processing page {i+1}/{len(pages)}...")
                
                # Configure Tesseract for better accuracy
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,:/%-() '
                
                page_text = pytesseract.image_to_string(page, config=custom_config)
                ocr_text_parts.append(page_text.strip())
            
            # Combine all pages
            full_ocr_text = "\n\n--- PAGE BREAK ---\n\n".join(ocr_text_parts)
            
            state["ocr_text"] = full_ocr_text
            state["processing_step"] = "ocr_extraction_complete"
            state["messages"].append(AIMessage(content=f"OCR extracted {len(full_ocr_text)} characters from {len(pages)} pages"))
            
            print(f"   ✅ OCR completed: {len(full_ocr_text)} characters extracted")
            
        except Exception as e:
            error_msg = f"OCR extraction error: {str(e)}"
            state["errors"].append(error_msg)
            state["ocr_text"] = ""
            print(f"   ❌ {error_msg}")
        
        return state
    
    def _parse_textract_node(self, state: AgentState) -> AgentState:
        """Parse and validate Textract JSON"""
        print("📄 Step 2: Parsing Textract JSON...")
        
        try:
            textract_data = state["textract_json"]
            
            # Validate required sections
            required_sections = ["file_info", "form_analysis", "table_analysis", "summary"]
            missing_sections = [section for section in required_sections if section not in textract_data]
            
            if missing_sections:
                state["errors"].append(f"Missing Textract sections: {missing_sections}")
            
            state["processing_step"] = "textract_parsing_complete"
            state["messages"].append(AIMessage(content="Textract JSON parsed successfully"))
            
            # Log extraction stats
            form_fields = textract_data.get("form_analysis", {}).get("total_fields", 0)
            tables = textract_data.get("table_analysis", {}).get("total_tables", 0)
            confidence = textract_data.get("summary", {}).get("confidence_score", 0)
            
            print(f"   ✅ Textract data: {form_fields} fields, {tables} tables, {confidence}% confidence")
            
        except Exception as e:
            state["errors"].append(f"Textract parsing error: {str(e)}")
        
        return state
    
    def _ai_extraction_node(self, state: AgentState) -> AgentState:
        """Extract entities using AI with both OCR and Textract data"""
        print("🤖 Step 3: AI extraction using dual sources...")
        
        try:
            if self.llm and state["ocr_text"] and len(state["ocr_text"]) > 50:
                try:
                    extracted_data = self._extract_with_ai_dual_source(
                        state["textract_json"], 
                        state["ocr_text"]
                    )
                    print("   ✅ AI extraction successful")
                except Exception as e:
                    print(f"   ⚠️  AI extraction failed: {e}, falling back to rule-based...")
                    extracted_data = self._extract_with_rules(state["textract_json"], state["ocr_text"])
            else:
                print("   Using rule-based extraction...")
                extracted_data = self._extract_with_rules(state["textract_json"], state["ocr_text"])
            
            state["extracted_data"] = extracted_data
            state["processing_step"] = "ai_extraction_complete"
            state["messages"].append(AIMessage(content="Entity extraction completed"))
            
        except Exception as e:
            error_msg = f"Entity extraction error: {str(e)}"
            state["errors"].append(error_msg)
            # Create minimal extracted data to prevent further errors
            state["extracted_data"] = ExtractedInvoiceData(
                document_type="INVOICE",
                filename=os.path.basename(state["pdf_path"]),
                confidence_score=0.0,
                ocr_text=state["ocr_text"]
            )
        
        return state
    
    def _extract_with_ai_dual_source(self, textract_data: Dict, ocr_text: str) -> ExtractedInvoiceData:
        """Use AI to extract structured data from both Textract JSON and OCR text"""
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert invoice processing AI. You have two data sources:
1. Textract JSON analysis (structured form fields and tables)  
2. Raw OCR text from the document

Your task: Extract accurate invoice information by cross-referencing both sources.

Extract EXACTLY these fields:
- Document details (type, filename, confidence)
- Company information (supplier and buyer names, GSTIN, addresses)
- Invoice details (number, date, amounts, taxes)
- Line items with quantities, rates, HSN codes
- Payment terms

Return ONLY valid JSON in this EXACT structure:
{{
    "document_type": "INVOICE",
    "filename": "filename.pdf",
    "confidence_score": 95.5,
    "supplier_name": "Company Name",
    "supplier_gstin": "GSTIN",
    "supplier_address": "Full address", 
    "buyer_name": "Buyer Company",
    "buyer_gstin": "Buyer GSTIN",
    "invoice_number": "INV-001",
    "invoice_date": "2024-11-07",
    "taxable_value": 100000.00,
    "total_tax": 18000.00,
    "total_amount": 118000.00,
    "line_items": [
        {{
            "description": "Product name",
            "hsn_code": "8471",
            "quantity": 2.0,
            "unit_price": 50000.0,
            "taxable_value": 100000.0,
            "gst_rate": 18.0,
            "gst_amount": 18000.0
        }}
    ],
    "payment_terms": "30 DAYS"
}}

CRITICAL RULES:
- Use null for missing values
- Extract exact numeric values (remove commas, currency symbols)
- Cross-validate data between Textract and OCR sources
- Prefer Textract structured data when available
- Use OCR text to fill gaps or verify accuracy
- Return "NO" as the entire response if no valid invoice data is found"""),
            ("human", """Extract invoice data using both sources:

TEXTRACT JSON:
{textract_data}

OCR TEXT:
{ocr_text}

Extract the invoice information in the required JSON format.""")
        ])
        
        parser = JsonOutputParser()
        chain = extraction_prompt | self.llm | parser
        
        try:
            result = chain.invoke({
                "textract_data": json.dumps(textract_data, indent=2),
                "ocr_text": ocr_text[:4000]  # Limit OCR text to avoid token limits
            })
            
            # Check if AI said NO
            if isinstance(result, str) and result.strip().upper() == "NO":
                raise ValueError("AI determined no valid invoice data found")
            
            # Convert to ExtractedInvoiceData
            return ExtractedInvoiceData(
                document_type=result.get("document_type", "INVOICE"),
                filename=result.get("filename", ""),
                confidence_score=result.get("confidence_score", 0.0),
                supplier_name=result.get("supplier_name"),
                supplier_gstin=result.get("supplier_gstin"),
                supplier_address=result.get("supplier_address"),
                buyer_name=result.get("buyer_name"),
                buyer_gstin=result.get("buyer_gstin"),
                invoice_number=result.get("invoice_number"),
                invoice_date=result.get("invoice_date"),
                taxable_value=result.get("taxable_value"),
                total_tax=result.get("total_tax"),
                total_amount=result.get("total_amount"),
                line_items=result.get("line_items", []),
                payment_terms=result.get("payment_terms"),
                raw_form_fields=textract_data.get("form_analysis", {}).get("form_fields", []),
                raw_tables=textract_data.get("table_analysis", {}).get("tables", []),
                ocr_text=ocr_text
            )
            
        except Exception as e:
            raise Exception(f"AI extraction failed: {e}")
    
    def _extract_with_rules(self, textract_data: Dict, ocr_text: str) -> ExtractedInvoiceData:
        """Rule-based extraction using both Textract and OCR data"""
        print("   Using rule-based extraction with dual sources...")
        
        form_fields = textract_data.get("form_analysis", {}).get("form_fields", [])
        file_info = textract_data.get("file_info", {})
        summary = textract_data.get("summary", {})
        
        # Create field lookup from Textract
        field_map = {field["key"].lower().strip(): field["value"] for field in form_fields if field["value"]}
        
        # Extract basic info
        extracted = ExtractedInvoiceData(
            document_type=summary.get("document_type", "INVOICE"),
            filename=file_info.get("filename", ""),
            confidence_score=summary.get("confidence_score", 0.0),
            raw_form_fields=form_fields,
            raw_tables=textract_data.get("table_analysis", {}).get("tables", []),
            ocr_text=ocr_text
        )
        
        # Enhanced extraction patterns
        invoice_patterns = {
            "invoice_number": ["invoice no.", "invoice num", "invoice number", "inv no"],
            "invoice_date": ["dated", "invoice date", "date"],
            "supplier_gstin": ["gstin/uin:", "gstin", "gstin/uin"],
            "taxable_value": ["taxable value", "amount"],
            "total_tax": ["total tax amount", "tax amount"],
            "payment_terms": ["mode/terms of payment", "payment terms"]
        }
        
        # Extract from Textract fields
        for attr, patterns in invoice_patterns.items():
            for pattern in patterns:
                if pattern in field_map:
                    value = field_map[pattern]
                    if attr in ["taxable_value", "total_tax"]:
                        value = self._clean_currency(value)
                    elif attr == "supplier_gstin":
                        extracted.supplier_gstin = value
                        continue
                    setattr(extracted, attr, value)
                    break
        
        # Try to extract missing data from OCR text
        if ocr_text:
            extracted = self._enhance_with_ocr_patterns(extracted, ocr_text)
        
        # Calculate total amount if missing
        if not extracted.total_amount and extracted.taxable_value and extracted.total_tax:
            extracted.total_amount = extracted.taxable_value + extracted.total_tax
        
        # Extract line items from tables
        extracted.line_items = self._extract_line_items_from_tables(
            textract_data.get("table_analysis", {}).get("tables", [])
        )
        
        return extracted
    
    def _enhance_with_ocr_patterns(self, extracted: ExtractedInvoiceData, ocr_text: str) -> ExtractedInvoiceData:
        """Enhance extracted data using OCR text patterns"""
        
        # Invoice number patterns
        if not extracted.invoice_number:
            inv_patterns = [
                r"Invoice\s+No\.?\s*:?\s*(\S+)",
                r"Bill\s+No\.?\s*:?\s*(\S+)",
                r"INV\s*[-#]?\s*(\S+)"
            ]
            for pattern in inv_patterns:
                match = re.search(pattern, ocr_text, re.IGNORECASE)
                if match:
                    extracted.invoice_number = match.group(1).strip()
                    break
        
        # GSTIN patterns
        if not extracted.supplier_gstin:
            gstin_pattern = r"GSTIN\s*:?\s*([A-Z0-9]{15})"
            match = re.search(gstin_pattern, ocr_text)
            if match:
                extracted.supplier_gstin = match.group(1)
        
        # Company name patterns
        if not extracted.supplier_name:
            # Look for company patterns
            company_patterns = [
                r"([A-Z][A-Z\s&]+(?:PVT\s+LTD|LIMITED|LLP|COMPANY))",
                r"([A-Z][A-Z\s]+ENGINEERING)",
                r"([A-Z][A-Z\s]+INDUSTRIES)"
            ]
            for pattern in company_patterns:
                match = re.search(pattern, ocr_text)
                if match:
                    extracted.supplier_name = match.group(1).strip()
                    break
        
        return extracted
    
    def _clean_currency(self, value: str) -> float:
        """Clean currency string and convert to float"""
        if not value:
            return 0.0
        
        # Remove currency symbols, commas, and extra spaces
        cleaned = re.sub(r'[₹,\s]', '', str(value))
        
        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def _extract_line_items_from_tables(self, tables: List[Dict]) -> List[Dict]:
        """Extract line items from table data"""
        line_items = []
        
        for table in tables:
            rows = table.get("rows", [])
            if len(rows) < 2:
                continue
            
            # Look for line item tables
            header = [str(cell).lower() for cell in rows[0]] if rows else []
            
            if any(keyword in " ".join(header) for keyword in ["hsn", "quantity", "rate", "amount"]):
                for row in rows[1:]:
                    if len(row) >= 4:
                        line_item = {
                            "description": str(row[0]) if len(row) > 0 else "",
                            "hsn_code": self._extract_hsn_code(row),
                            "quantity": self._extract_number(str(row[3]) if len(row) > 3 else "0"),
                            "unit_price": self._clean_currency(str(row[4]) if len(row) > 4 else "0"),
                            "taxable_value": self._clean_currency(str(row[6]) if len(row) > 6 else "0")
                        }
                        
                        if line_item["description"] and line_item["description"] not in ["Total", "TOTAL"]:
                            line_items.append(line_item)
        
        return line_items
    
    def _extract_hsn_code(self, row: List) -> str:
        """Extract HSN code from table row"""
        for cell in row:
            cell_str = str(cell)
            if re.match(r'^\d{4,8}$', cell_str):  # HSN codes are typically 4-8 digits
                return cell_str
        return ""
    
    def _extract_number(self, value: str) -> float:
        """Extract number from string"""
        if not value:
            return 0.0
        
        numbers = re.findall(r'[\d.]+', str(value))
        if numbers:
            try:
                return float(numbers[0])
            except ValueError:
                pass
        return 0.0
    
    def _validate_data_node(self, state: AgentState) -> AgentState:
        """Validate extracted data with strict requirements"""
        print("✅ Step 4: Validating extracted data...")
        
        extracted = state["extracted_data"]
        errors = []
        
        if not extracted:
            errors.append("No data extracted")
            state["errors"].extend(errors)
            return state
        
        # Strict validation - if no valid data found, say NO
        if not extracted.invoice_number and not extracted.taxable_value and not extracted.supplier_gstin:
            errors.append("NO valid invoice data found - insufficient information")
        
        if extracted.invoice_number and not re.match(r'[A-Z0-9/-]+', extracted.invoice_number):
            errors.append(f"Invalid invoice number format: {extracted.invoice_number}")
        
        if extracted.taxable_value and extracted.taxable_value <= 0:
            errors.append("Invalid taxable value")
        
        # Add validation errors to state
        state["errors"].extend(errors)
        state["processing_step"] = "validation_complete"
        
        if not errors:
            state["messages"].append(AIMessage(content="Data validation passed"))
        else:
            state["messages"].append(AIMessage(content=f"Validation issues: {len(errors)} problems found"))
        
        return state
    
    def _store_database_node(self, state: AgentState) -> AgentState:
        """Store extracted data in database (only if valid)"""
        print("💾 Step 5: Storing data in database...")
        
        # Check if validation failed
        validation_errors = [e for e in state["errors"] if "NO valid invoice data" in e]
        if validation_errors:
            print("   ❌ Skipping database storage - no valid invoice data found")
            state["processing_step"] = "database_storage_skipped"
            return state
        
        try:
            extracted = state["extracted_data"]
            if not extracted or not extracted.invoice_number:
                state["errors"].append("No valid data to store")
                return state
                
            cursor = self.db.conn.cursor()
            cursor.execute("BEGIN TRANSACTION")
            
            # Store document with full OCR text
            cursor.execute("""
                INSERT INTO documents (doc_type, filename, file_size_bytes, analysis_confidence, raw_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                extracted.document_type or "INVOICE",
                extracted.filename or os.path.basename(state["pdf_path"]),
                os.path.getsize(state["pdf_path"]) if os.path.exists(state["pdf_path"]) else None,
                extracted.confidence_score or 0.0,
                json.dumps({
                    "textract_data": state["textract_json"],
                    "ocr_text": extracted.ocr_text,
                    "extraction_method": "dual_source"
                })
            ))
            doc_id = cursor.lastrowid
            
            # Store company information
            supplier_id = self._insert_or_get_company(cursor, {
                "legal_name": extracted.supplier_name or "Unknown Supplier",
                "gstin": extracted.supplier_gstin,
                "address": extracted.supplier_address
            })
            
            buyer_id = None
            if extracted.buyer_name:
                buyer_id = self._insert_or_get_company(cursor, {
                    "legal_name": extracted.buyer_name,
                    "gstin": extracted.buyer_gstin
                })
            
            # Store invoice
            cursor.execute("""
                INSERT INTO invoices 
                (doc_id, invoice_num, invoice_date, supplier_company_id, buyer_company_id, 
                 taxable_value, total_tax, total_value, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id,
                extracted.invoice_number,
                self._parse_date(extracted.invoice_date),
                supplier_id,
                buyer_id,
                extracted.taxable_value or 0.0,
                extracted.total_tax or 0.0,
                extracted.total_amount or 0.0,
                'PROCESSED'
            ))
            invoice_id = cursor.lastrowid
            
            # Store line items
            for item in extracted.line_items or []:
                product_id = self._insert_or_get_product(cursor, item)
                
                cursor.execute("""
                    INSERT INTO invoice_item 
                    (invoice_id, product_id, hsn_code, item_description, quantity, 
                     unit_price, taxable_value, gst_rate, gst_amount, total_amount)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    invoice_id,
                    product_id,
                    item.get("hsn_code"),
                    item.get("description"),
                    item.get("quantity", 0),
                    item.get("unit_price", 0),
                    item.get("taxable_value", 0),
                    item.get("gst_rate", 18),
                    item.get("gst_amount", 0),
                    (item.get("taxable_value", 0) or 0) + (item.get("gst_amount", 0) or 0)
                ))
            
            cursor.execute("COMMIT")
            
            state["database_ids"] = {
                "doc_id": doc_id,
                "invoice_id": invoice_id,
                "supplier_id": supplier_id,
                "buyer_id": buyer_id
            }
            
            state["processing_step"] = "database_storage_complete"
            state["messages"].append(AIMessage(content=f"Data stored successfully. Invoice ID: {invoice_id}"))
            print(f"   ✅ Stored invoice {extracted.invoice_number} with ID {invoice_id}")
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            error_msg = f"Database storage error: {str(e)}"
            state["errors"].append(error_msg)
            print(f"   ❌ {error_msg}")
        
        return state
    
    def _insert_or_get_company(self, cursor: sqlite3.Cursor, company_data: Dict) -> int:
        """Insert company or get existing ID"""
        gstin = company_data.get("gstin")
        
        if gstin:
            cursor.execute("SELECT company_id FROM companies WHERE gstin = ?", (gstin,))
            result = cursor.fetchone()
            if result:
                return result[0]
        
        cursor.execute("""
            INSERT INTO companies (legal_name, gstin, address)
            VALUES (?, ?, ?)
        """, (
            company_data.get("legal_name", "Unknown"),
            gstin,
            company_data.get("address")
        ))
        return cursor.lastrowid
    
    def _insert_or_get_product(self, cursor: sqlite3.Cursor, item_data: Dict) -> Optional[int]:
        """Insert product or get existing ID"""
        hsn_code = item_data.get("hsn_code")
        description = item_data.get("description", "").strip()
        
        if hsn_code and description:
            cursor.execute("""
                SELECT product_id FROM products 
                WHERE hsn_code = ? AND canonical_name = ?
            """, (hsn_code, description))
            result = cursor.fetchone()
            if result:
                return result[0]
            
            cursor.execute("""
                INSERT INTO products (canonical_name, hsn_code, description)
                VALUES (?, ?, ?)
            """, (description, hsn_code, description))
            return cursor.lastrowid
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string to standard format"""
        if not date_str:
            return None
        
        patterns = [
            r"(\d{1,2})-(\w{3})-(\d{2})",  # 5-Mar-25
            r"(\d{1,2})-(\d{1,2})-(\d{4})",  # 5-3-2025
            r"(\d{4})-(\d{1,2})-(\d{1,2})"   # 2025-3-5
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if "Mar" in date_str or "Jan" in date_str:  # Handle month names
                        month_map = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                                   "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
                        day, month_str, year = match.groups()
                        year = "20" + year if len(year) == 2 else year
                        month = month_map.get(month_str, 1)
                        return f"{year}-{month:02d}-{int(day):02d}"
                    else:
                        parts = match.groups()
                        if len(parts[2]) == 2:
                            return f"20{parts[2]}-{int(parts[1]):02d}-{int(parts[0]):02d}"
                        else:
                            return f"{parts[0]}-{int(parts[1]):02d}-{int(parts[2]):02d}"
                except:
                    continue
        
        return date_str
    
    def _update_memory_node(self, state: AgentState) -> AgentState:
        """Update agent memory with processing insights"""
        print("🧠 Step 6: Updating memory...")
        
        memory_entry = {
            "timestamp": datetime.now().isoformat(),
            "document_type": state["extracted_data"].document_type if state["extracted_data"] else "UNKNOWN",
            "processing_success": len([e for e in state["errors"] if "NO valid invoice data" not in e]) == 0,
            "confidence_score": state["extracted_data"].confidence_score if state["extracted_data"] else 0,
            "ocr_chars_extracted": len(state["ocr_text"]),
            "fields_extracted": len(state["extracted_data"].raw_form_fields or []) if state["extracted_data"] else 0,
            "tables_processed": len(state["extracted_data"].raw_tables or []) if state["extracted_data"] else 0,
            "line_items_count": len(state["extracted_data"].line_items or []) if state["extracted_data"] else 0,
            "extraction_method": "ai" if self.llm else "rule_based",
            "errors": state["errors"]
        }
        
        state["memory_updates"].append(memory_entry)
        state["processing_step"] = "memory_update_complete"
        state["messages"].append(AIMessage(content="Memory updated with processing insights"))
        
        return state
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize processing and prepare response"""
        print("🎯 Step 7: Finalizing processing...")
        
        state["processing_step"] = "complete"
        
        # Check if we found NO valid data
        validation_errors = [e for e in state["errors"] if "NO valid invoice data" in e]
        if validation_errors:
            state["messages"].append(AIMessage(content="NO - No valid invoice data found in document"))
            return state
        
        # Generate success summary
        success = len([e for e in state["errors"] if "NO valid invoice data" not in e]) == 0
        summary = {
            "success": success,
            "document_processed": state["extracted_data"].filename if state["extracted_data"] else "unknown",
            "invoice_number": state["extracted_data"].invoice_number if state["extracted_data"] else None,
            "database_ids": state["database_ids"],
            "errors": state["errors"],
            "memory_entries": len(state["memory_updates"])
        }
        
        status_msg = "✅ Processing completed successfully" if success else "⚠️  Processing completed with issues"
        state["messages"].append(AIMessage(content=f"{status_msg}\nSummary: {json.dumps(summary, indent=2)}"))
        
        return state
    
    def process_pdf_with_textract_json(self, pdf_path: str, textract_json_path: str) -> Dict[str, Any]:
        """Main method to process PDF with Textract JSON"""
        print(f"🚀 Processing PDF with dual sources:")
        print(f"   PDF: {pdf_path}")
        print(f"   Textract JSON: {textract_json_path}")
        print("=" * 80)
        
        # Validate files exist
        if not os.path.exists(pdf_path):
            return {"error": f"PDF file not found: {pdf_path}"}
        
        if not os.path.exists(textract_json_path):
            return {"error": f"Textract JSON file not found: {textract_json_path}"}
        
        # Load Textract JSON
        try:
            with open(textract_json_path, 'r', encoding='utf-8') as f:
                textract_json = json.load(f)
        except Exception as e:
            return {"error": f"Failed to load Textract JSON: {e}"}
        
        # Initialize state
        initial_state = {
            "pdf_path": pdf_path,
            "textract_json": textract_json,
            "ocr_text": "",
            "extracted_data": None,
            "database_ids": {},
            "messages": [HumanMessage(content=f"Process {pdf_path} with dual extraction")],
            "errors": [],
            "processing_step": "initialized",
            "memory_updates": []
        }
        
        # Run the processing graph
        try:
            final_state = self.graph.invoke(
                initial_state, 
                config={"configurable": {"thread_id": f"dual_processing_{int(datetime.now().timestamp())}"}}
            )
            
            # Check if NO valid data was found
            validation_errors = [e for e in final_state["errors"] if "NO valid invoice data" in e]
            if validation_errors:
                print("\n" + "=" * 80)
                print("❌ RESULT: NO")
                print("   No valid invoice data found in document")
                print("=" * 80)
                return {"result": "NO", "reason": "No valid invoice data found"}
            
            # Print results
            self._print_processing_results(final_state)
            
            success = len([e for e in final_state["errors"] if "NO valid invoice data" not in e]) == 0
            return {
                "success": success,
                "extracted_data": final_state["extracted_data"],
                "database_ids": final_state["database_ids"],
                "errors": final_state["errors"],
                "memory_updates": final_state["memory_updates"],
                "ocr_text": final_state["ocr_text"]
            }
            
        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
    
    def _print_processing_results(self, final_state: AgentState):
        """Print formatted processing results"""
        print("\n" + "=" * 80)
        print("📊 DUAL-SOURCE PROCESSING RESULTS")
        print("=" * 80)
        
        extracted = final_state["extracted_data"]
        if extracted:
            print(f"📄 Document: {extracted.filename}")
            print(f"🏷️  Invoice: {extracted.invoice_number or 'Not found'}")
            print(f"📅 Date: {extracted.invoice_date or 'Not found'}")
            print(f"💰 Total: ₹{extracted.total_amount:,.2f}" if extracted.total_amount else "Not found")
            print(f"🏢 Supplier: {extracted.supplier_name or 'Not found'}")
            print(f"🆔 GSTIN: {extracted.supplier_gstin or 'Not found'}")
            print(f"🎯 Confidence: {extracted.confidence_score}%")
            print(f"📝 OCR Text: {len(extracted.ocr_text or '')} characters")
            print(f"📋 Line Items: {len(extracted.line_items or [])} items")
        
        if final_state["database_ids"]:
            print(f"\n💾 Database Records:")
            for key, value in final_state["database_ids"].items():
                print(f"   {key}: {value}")
        
        if final_state["errors"]:
            print(f"\n⚠️  Issues ({len(final_state['errors'])}):")
            for error in final_state["errors"]:
                print(f"   • {error}")
        
        print(f"\n🧠 Memory Updates: {len(final_state['memory_updates'])} entries")
        print("=" * 80)

def main():
    """Main function for testing the enhanced agent"""
    if len(sys.argv) != 3:
        print("Usage: python enhanced_invoice_ai_agent.py <pdf_file> <textract_json_file>")
        print("Example: python enhanced_invoice_ai_agent.py 1.pdf textract_analysis_1_20251107_181228.json")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    json_file = sys.argv[2]
    
    if not os.path.exists(pdf_file):
        print(f"❌ PDF file not found: {pdf_file}")
        sys.exit(1)
    
    if not os.path.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        sys.exit(1)
    
    # Initialize agent
    agent = EnhancedInvoiceAIAgent()
    
    # Process the files
    result = agent.process_pdf_with_textract_json(pdf_file, json_file)
    
    if result.get("result") == "NO":
        print(f"\n❌ Result: NO - {result.get('reason', 'No valid invoice data found')}")
    elif result.get("success"):
        print("\n✅ Processing completed successfully!")
    else:
        print(f"\n❌ Processing failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()