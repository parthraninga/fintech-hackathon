#!/usr/bin/env python3
"""
Intelligent Document Classification System

This module provides AI-powered document type classification for various
business document types including invoices, expense slips, payment proofs, etc.

Supported Document Types:
- B2B_INVOICE: Business-to-business invoices
- EXPENSE_SLIP: Expense receipts and slips
- PAYMENT_PROOF: Payment confirmations, bank transfers, etc.
- PURCHASE_ORDER: Purchase orders and procurement documents
- CREDIT_NOTE: Credit notes and return documents
- DEBIT_NOTE: Debit notes and charge documents
- QUOTATION: Price quotes and estimates

Features:
1. AI-powered classification using document content analysis
2. Rule-based classification for fallback
3. Confidence scoring for classification accuracy
4. Multi-language support for Indian business documents
5. Integration with database storage and metadata management
6. NO UNKNOWN TYPE - Always classifies into one of the specific categories
"""

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DocumentClassificationResult:
    """Result of document classification analysis"""
    document_type: str
    confidence_score: float
    classification_reasoning: List[str]
    detected_keywords: List[str]
    alternate_types: List[Dict[str, float]]
    metadata: Dict[str, Any]

class DocumentClassifier:
    """Intelligent document type classifier"""
    
    def __init__(self):
        """Initialize the document classifier with patterns and keywords"""
        self.document_types = {
            "B2B_INVOICE": {
                "confidence_threshold": 0.5,  # Reduced threshold for better detection
                "keywords": [
                    "invoice", "bill", "tax invoice", "commercial invoice", 
                    "gstin", "gst", "invoice number", "invoice no", "bill no",
                    "taxable value", "igst", "cgst", "sgst", "supplier",
                    "buyer", "invoice date", "due date", "payment terms",
                    "pvt ltd", "private limited", "company", "corporation",
                    "total", "amount", "quantity", "rate", "hsn"
                ],
                "patterns": [
                    r"invoice\s*(no|number|#)",
                    r"tax\s*invoice", 
                    r"commercial\s*invoice",
                    r"gstin[:]*\s*\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}",  # More flexible GSTIN pattern
                    r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}",  # GSTIN without prefix
                    r"(cgst|sgst|igst)",
                    r"taxable\s*(value|amount)",
                    r"hsn\s*(code|no)",
                    r"(pvt\.?\s*ltd|private\s*limited)",  # Company indicators
                    r"₹\s*[\d,]+\.?\d*",  # Indian currency amounts
                    r"rs\.?\s*[\d,]+\.?\d*",  # Rupees amounts
                    r"\d{2}[-/]\w{3}[-/]\d{2,4}",  # Date patterns like 20-Aug-25
                    r"[A-Z]{2,}[/-]\d{2}[-/]\d{2}[/-]\d+",  # Invoice number patterns like SBD/25-26/197
                ],
                "negative_keywords": ["receipt", "expense", "reimbursement", "petty cash"],
                # Strong indicators that boost confidence significantly
                "strong_indicators": [
                    r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}",  # GSTIN format
                    r"(pvt\.?\s*ltd|private\s*limited)",  # Company type
                    r"(cgst|sgst|igst)\s*[:@]\s*[\d.]+%?",  # Tax rates
                    r"taxable\s*(value|amount)",  # Business terminology
                    r"invoice\s*(no|number)",  # Invoice numbering
                ]
            },
            "EXPENSE_SLIP": {
                "confidence_threshold": 0.6,
                "keywords": [
                    "expense", "receipt", "reimbursement", "petty cash",
                    "travel", "food", "fuel", "conveyance", "hotel",
                    "taxi", "auto", "cab", "meal", "breakfast", "lunch", "dinner",
                    "parking", "toll", "medical", "medicine", "doctor",
                    "stationery", "office supplies"
                ],
                "patterns": [
                    r"expense\s*(receipt|slip)",
                    r"reimbursement",
                    r"petty\s*cash",
                    r"travel\s*(expense|bill)",
                    r"hotel\s*(bill|receipt)",
                    r"taxi\s*(receipt|bill)",
                    r"fuel\s*(receipt|bill)"
                ],
                "negative_keywords": ["invoice", "commercial", "tax invoice"]
            },
            "PAYMENT_PROOF": {
                "confidence_threshold": 0.6,
                "keywords": [
                    "payment", "paid", "transaction", "transfer", "upi",
                    "neft", "rtgs", "imps", "bank", "payment successful",
                    "transaction id", "reference number", "utr number",
                    "credited", "debited", "account", "paytm", "phonepe",
                    "googlepay", "razorpay", "payment confirmation"
                ],
                "patterns": [
                    r"payment\s*(successful|confirmed|completed)",
                    r"transaction\s*(id|reference)",
                    r"utr\s*(no|number)",
                    r"(neft|rtgs|imps|upi)",
                    r"credited.*account",
                    r"debited.*account",
                    r"payment\s*of.*rs"
                ],
                "negative_keywords": ["invoice", "bill", "expense"]
            },
            "PURCHASE_ORDER": {
                "confidence_threshold": 0.7,
                "keywords": [
                    "purchase order", "po", "order", "procurement",
                    "vendor", "supplier", "delivery", "shipment",
                    "order number", "po number", "delivery date",
                    "terms and conditions", "specifications"
                ],
                "patterns": [
                    r"purchase\s*order",
                    r"p\.?o\.?\s*(no|number)",
                    r"order\s*(no|number)",
                    r"delivery\s*date",
                    r"procurement"
                ],
                "negative_keywords": ["invoice", "payment", "receipt"]
            },
            "CREDIT_NOTE": {
                "confidence_threshold": 0.8,
                "keywords": [
                    "credit note", "credit memo", "return", "refund",
                    "credit", "adjustment", "discount", "allowance"
                ],
                "patterns": [
                    r"credit\s*(note|memo)",
                    r"return\s*(note|memo)",
                    r"refund",
                    r"credit\s*adjustment"
                ],
                "negative_keywords": ["invoice", "debit"]
            },
            "DEBIT_NOTE": {
                "confidence_threshold": 0.8,
                "keywords": [
                    "debit note", "debit memo", "charge", "additional charges",
                    "penalty", "interest", "late fee"
                ],
                "patterns": [
                    r"debit\s*(note|memo)",
                    r"additional\s*charge",
                    r"penalty",
                    r"late\s*fee"
                ],
                "negative_keywords": ["credit", "refund"]
            },
            "QUOTATION": {
                "confidence_threshold": 0.7,
                "keywords": [
                    "quotation", "quote", "estimate", "proposal",
                    "price list", "rate card", "offer", "proforma",
                    "validity", "terms", "specifications"
                ],
                "patterns": [
                    r"quotation\s*(no|number)",
                    r"quote\s*(no|number)",
                    r"estimate",
                    r"proforma\s*invoice",
                    r"price\s*(quote|quotation)"
                ],
                "negative_keywords": ["invoice", "payment", "receipt"]
            }
        }
    
    def classify_document(self, textract_data: Dict, ocr_text: str, filename: str = "") -> DocumentClassificationResult:
        """
        Classify document type based on textract data and OCR text
        
        Args:
            textract_data: Structured data from AWS Textract
            ocr_text: Raw OCR text from the document
            filename: Original filename for additional context
            
        Returns:
            DocumentClassificationResult with classification details
        """
        
        print(f"📄 Classifying document type...")
        
        # Prepare text for analysis
        analysis_text = self._prepare_text_for_analysis(textract_data, ocr_text, filename)
        
        # Score each document type
        type_scores = {}
        classification_details = {}
        
        for doc_type, config in self.document_types.items():
            score, details = self._score_document_type(analysis_text, doc_type, config)
            type_scores[doc_type] = score
            classification_details[doc_type] = details
        
        # Determine best classification
        best_type = max(type_scores, key=type_scores.get)
        best_score = type_scores[best_type]
        best_details = classification_details[best_type]
        
        # NO UNKNOWN TYPE - Always classify into a specific type
        # Special handling for B2B invoices - reduce threshold if strong indicators present
        if best_type == "B2B_INVOICE" and best_details.get("strong_matches"):
            confidence_threshold = min(self.document_types[best_type]["confidence_threshold"], 0.4)
        else:
            confidence_threshold = self.document_types[best_type]["confidence_threshold"]
        
        # Force classification even if below threshold - no UNKNOWN type
        if best_score < confidence_threshold:
            # Boost the score slightly but provide reasoning for forced classification
            best_details["reasoning"].insert(0, 
                f"Force-classified as {best_type} with {best_score:.1%} confidence (threshold: {confidence_threshold:.1%})")
            best_details["reasoning"].append("No UNKNOWN classification - assigned to best matching type")
            
            # Boost confidence to minimum acceptable level
            best_score = max(best_score, 0.6)
        else:
            # Add confidence boost explanation for strong classifications
            if best_score > 0.75:
                best_details["reasoning"].insert(0, 
                    f"Document classified as {best_type} with {best_score:.1%} confidence - above {confidence_threshold:.1%} threshold")
        
        # Create alternate types list (excluding the chosen type)
        alternate_types = [
            {"type": doc_type, "score": score} 
            for doc_type, score in sorted(type_scores.items(), key=lambda x: x[1], reverse=True)
            if doc_type != best_type and score > 0.2  # Lower threshold for alternatives
        ][:3]  # Top 3 alternates
        
        # Extract metadata
        metadata = self._extract_document_metadata(textract_data, ocr_text, best_type)
        
        result = DocumentClassificationResult(
            document_type=best_type,
            confidence_score=best_score,
            classification_reasoning=best_details["reasoning"],
            detected_keywords=best_details["matched_keywords"],
            alternate_types=alternate_types,
            metadata=metadata
        )
        
        # Print classification results
        self._print_classification_results(result, filename)
        
        return result
    
    def _prepare_text_for_analysis(self, textract_data: Dict, ocr_text: str, filename: str) -> str:
        """Prepare comprehensive text for document analysis"""
        text_parts = []
        
        # Add filename
        if filename:
            text_parts.append(filename.lower())
        
        # Add form fields from textract
        if "form_analysis" in textract_data:
            form_fields = textract_data["form_analysis"].get("form_fields", [])
            for field in form_fields:
                if field.get("key"):
                    text_parts.append(field["key"].lower())
                if field.get("value"):
                    text_parts.append(field["value"].lower())
        
        # Add table data from textract
        if "table_analysis" in textract_data:
            tables = textract_data["table_analysis"].get("tables", [])
            for table in tables:
                if isinstance(table, dict) and "rows" in table:
                    # Standard textract format
                    for row in table.get("rows", []):
                        for cell in row:
                            text_parts.append(str(cell).lower())
                elif isinstance(table, list):
                    # Simple list format (test data)
                    for row in table:
                        if isinstance(row, list):
                            for cell in row:
                                text_parts.append(str(cell).lower())
        
        # Add OCR text
        if ocr_text:
            text_parts.append(ocr_text.lower())
        
        # Add summary data
        if "summary" in textract_data:
            summary = textract_data["summary"]
            if summary.get("document_type"):
                text_parts.append(summary["document_type"].lower())
            if summary.get("key_entities"):
                text_parts.extend([str(entity).lower() for entity in summary["key_entities"]])
        
        return " ".join(text_parts)
    
    def _score_document_type(self, text: str, doc_type: str, config: Dict) -> Tuple[float, Dict]:
        """Score how well the text matches a specific document type"""
        matched_keywords = []
        matched_patterns = []
        negative_matches = []
        strong_matches = []
        reasoning = []
        
        # Check keywords
        keyword_score = 0
        for keyword in config["keywords"]:
            if keyword in text:
                matched_keywords.append(keyword)
                # Weight important business keywords more highly
                if keyword in ["gstin", "pvt ltd", "private limited", "taxable value", "cgst", "sgst", "igst"]:
                    weight = 2.0  # High weight for business indicators
                elif keyword in ["invoice", "bill", "supplier", "company"]:
                    weight = 1.5  # Medium weight for document type indicators
                else:
                    weight = 1.0  # Standard weight
                keyword_score += weight
        
        keyword_score = min(keyword_score / (len(config["keywords"]) * 1.5), 1.0)
        
        # Check patterns
        pattern_score = 0
        for pattern in config["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                matched_patterns.append(pattern)
                pattern_score += 1.0
        
        pattern_score = min(pattern_score / len(config["patterns"]), 1.0)
        
        # Check strong indicators (for B2B invoices)
        strong_indicator_bonus = 0
        if "strong_indicators" in config:
            for indicator in config["strong_indicators"]:
                if re.search(indicator, text, re.IGNORECASE):
                    strong_matches.append(indicator)
                    strong_indicator_bonus += 0.15  # 15% bonus per strong indicator
        
        strong_indicator_bonus = min(strong_indicator_bonus, 0.4)  # Max 40% bonus
        
        # Check negative keywords (reduce score)
        negative_penalty = 0
        negative_keywords = config.get("negative_keywords", [])
        for neg_keyword in negative_keywords:
            if neg_keyword in text:
                negative_matches.append(neg_keyword)
                negative_penalty += 0.1  # Reduced penalty from 0.2 to 0.1
        
        negative_penalty = min(negative_penalty, 0.3)  # Reduced max penalty from 0.8 to 0.3
        
        # Calculate final score with enhanced logic
        base_score = (keyword_score * 0.5 + pattern_score * 0.3 + strong_indicator_bonus * 0.2)
        final_score = max(0, base_score + strong_indicator_bonus - negative_penalty)
        
        # Boost score for very strong B2B indicators
        if doc_type == "B2B_INVOICE" and strong_matches:
            gstin_pattern = r"\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}"
            company_pattern = r"(pvt\.?\s*ltd|private\s*limited)"
            tax_pattern = r"(cgst|sgst|igst)"
            
            if (re.search(gstin_pattern, text, re.IGNORECASE) and 
                re.search(company_pattern, text, re.IGNORECASE) and 
                re.search(tax_pattern, text, re.IGNORECASE)):
                final_score = max(final_score, 0.85)  # Guarantee high confidence for strong B2B signals
                reasoning.append("Strong B2B invoice indicators: Valid GSTIN + Company type + Tax details")
        
        # Generate detailed reasoning
        if matched_keywords:
            key_words = [kw for kw in matched_keywords if kw in ["gstin", "pvt ltd", "taxable value", "cgst", "sgst", "igst", "invoice"]]
            if key_words:
                reasoning.append(f"Key business terms found: {', '.join(key_words[:5])}")
            else:
                reasoning.append(f"Relevant keywords found: {', '.join(matched_keywords[:5])}")
        
        if strong_matches:
            reasoning.append(f"Strong {doc_type} indicators detected: {len(strong_matches)} patterns")
        
        if matched_patterns:
            reasoning.append(f"Matched {len(matched_patterns)} document structure patterns")
        
        if negative_matches:
            reasoning.append(f"Some conflicting terms found: {', '.join(negative_matches)} (minor impact)")
        
        # Enhanced confidence reasoning
        if final_score > 0.8:
            reasoning.append(f"Very high confidence {doc_type} classification")
        elif final_score > 0.65:
            reasoning.append(f"High confidence {doc_type} classification")
        elif final_score > 0.5:
            reasoning.append(f"Moderate confidence {doc_type} classification")
        else:
            reasoning.append(f"Low confidence {doc_type} classification")
        
        return final_score, {
            "matched_keywords": matched_keywords,
            "matched_patterns": matched_patterns,
            "strong_matches": strong_matches,
            "negative_matches": negative_matches,
            "reasoning": reasoning
        }
    
    def _extract_document_metadata(self, textract_data: Dict, ocr_text: str, doc_type: str) -> Dict[str, Any]:
        """Extract relevant metadata based on document type"""
        metadata = {
            "classification_timestamp": datetime.now().isoformat(),
            "text_length": len(ocr_text) if ocr_text else 0,
            "has_form_fields": bool(textract_data.get("form_analysis", {}).get("form_fields")),
            "has_tables": bool(textract_data.get("table_analysis", {}).get("tables")),
            "document_language": self._detect_language(ocr_text or "")
        }
        
        # Document type specific metadata
        if doc_type == "B2B_INVOICE":
            metadata.update({
                "has_gstin": bool(re.search(r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d[Z]{1}[A-Z\d]{1}', ocr_text or "")),
                "has_tax_details": bool(re.search(r'(cgst|sgst|igst)', ocr_text or "", re.IGNORECASE)),
                "has_invoice_number": bool(re.search(r'invoice\s*(no|number)', ocr_text or "", re.IGNORECASE))
            })
        elif doc_type == "PAYMENT_PROOF":
            metadata.update({
                "has_transaction_id": bool(re.search(r'(transaction|utr|reference).*id', ocr_text or "", re.IGNORECASE)),
                "has_amount": bool(re.search(r'(rs|₹|inr).*\d', ocr_text or "", re.IGNORECASE)),
                "payment_method": self._detect_payment_method(ocr_text or "")
            })
        elif doc_type == "EXPENSE_SLIP":
            metadata.update({
                "expense_category": self._detect_expense_category(ocr_text or ""),
                "has_amount": bool(re.search(r'(rs|₹|inr|total).*\d', ocr_text or "", re.IGNORECASE))
            })
        
        return metadata
    
    def _detect_language(self, text: str) -> str:
        """Detect document language (basic detection)"""
        # Simple language detection based on character patterns
        if re.search(r'[α-ωΑ-Ω]', text):  # Greek characters (common in some Indian scripts)
            return "multilingual"
        elif re.search(r'[^\x00-\x7F]', text):  # Non-ASCII characters
            return "multilingual"
        else:
            return "english"
    
    def _detect_payment_method(self, text: str) -> Optional[str]:
        """Detect payment method from text"""
        methods = {
            "UPI": r"(upi|phonepe|paytm|googlepay|bhim)",
            "NEFT": r"neft",
            "RTGS": r"rtgs", 
            "IMPS": r"imps",
            "CARD": r"(card|visa|master|rupay)",
            "CASH": r"cash",
            "CHEQUE": r"(cheque|check)"
        }
        
        for method, pattern in methods.items():
            if re.search(pattern, text, re.IGNORECASE):
                return method
        
        return "UNKNOWN"
    
    def _detect_expense_category(self, text: str) -> Optional[str]:
        """Detect expense category from text"""
        categories = {
            "TRAVEL": r"(travel|taxi|cab|auto|bus|train|flight|hotel|accommodation)",
            "FOOD": r"(food|meal|breakfast|lunch|dinner|restaurant|cafe)",
            "FUEL": r"(fuel|petrol|diesel|gas|cng)",
            "MEDICAL": r"(medical|doctor|hospital|medicine|pharmacy)",
            "OFFICE": r"(stationery|office|supplies|equipment)",
            "COMMUNICATION": r"(mobile|phone|internet|broadband)",
            "ENTERTAINMENT": r"(entertainment|movie|event)"
        }
        
        for category, pattern in categories.items():
            if re.search(pattern, text, re.IGNORECASE):
                return category
        
        return "GENERAL"
    
    def _print_classification_results(self, result: DocumentClassificationResult, filename: str = ""):
        """Print formatted classification results"""
        print(f"📋 DOCUMENT CLASSIFICATION RESULTS:")
        print("-" * 50)
        
        if filename:
            print(f"File: {filename}")
        
        print(f"Document Type: {result.document_type}")
        print(f"Confidence: {result.confidence_score:.1%}")
        
        # Print detailed reasoning
        if result.classification_reasoning:
            print(f"Reasoning:")
            for reason in result.classification_reasoning:
                print(f"  • {reason}")
        
        if result.detected_keywords:
            print(f"Keywords Found: {', '.join(result.detected_keywords[:10])}")
        
        if result.alternate_types:
            print(f"Alternate Types:")
            for alt in result.alternate_types:
                print(f"  • {alt['type']}: {alt['score']:.1%}")
        
        # Show metadata highlights for all document types
        if result.metadata:
            highlights = []
            if result.document_type == "B2B_INVOICE":
                if result.metadata.get("has_gstin"):
                    highlights.append("✓ Valid GSTIN format")
                if result.metadata.get("has_tax_details"):
                    highlights.append("✓ Tax structure present")
                if result.metadata.get("has_invoice_number"):
                    highlights.append("✓ Invoice numbering")
            elif result.document_type == "PAYMENT_PROOF":
                if result.metadata.get("has_transaction_id"):
                    highlights.append("✓ Transaction ID present")
                if result.metadata.get("payment_method"):
                    highlights.append(f"✓ Payment method: {result.metadata['payment_method']}")
            elif result.document_type == "EXPENSE_SLIP":
                if result.metadata.get("expense_category"):
                    highlights.append(f"✓ Category: {result.metadata['expense_category']}")
                if result.metadata.get("has_amount"):
                    highlights.append("✓ Amount present")
            
            if highlights:
                print(f"Document Indicators: {', '.join(highlights)}")
        
        print("-" * 50)

def main():
    """Test the document classifier"""
    print("📄 DOCUMENT CLASSIFICATION SYSTEM TEST")
    print("=" * 60)
    
    classifier = DocumentClassifier()
    
    # Test with sample data
    test_cases = [
        {
            "filename": "invoice_001.pdf",
            "textract": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Invoice Number", "value": "INV-2024-001"},
                        {"key": "GSTIN", "value": "29ABCDE1234F1Z5"},
                        {"key": "Taxable Value", "value": "100000"}
                    ]
                },
                "summary": {"document_type": "Invoice"}
            },
            "ocr_text": "Tax Invoice Invoice No: INV-2024-001 GSTIN: 29ABCDE1234F1Z5 Taxable Value: 100000 CGST: 9000 SGST: 9000"
        },
        {
            "filename": "expense_receipt.pdf", 
            "textract": {
                "form_analysis": {
                    "form_fields": [
                        {"key": "Receipt", "value": "Taxi Fare"},
                        {"key": "Amount", "value": "250"}
                    ]
                }
            },
            "ocr_text": "Taxi Receipt Travel Expense Amount: Rs 250 Reimbursement claim"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {test_case['filename']}")
        print("-" * 40)
        
        result = classifier.classify_document(
            test_case["textract"],
            test_case["ocr_text"], 
            test_case["filename"]
        )

if __name__ == "__main__":
    main()