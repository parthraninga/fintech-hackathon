#!/usr/bin/env python3
"""
Intelligent Duplication Detection System for Invoice Processing

This module provides AI-powered duplicate detection that analyzes multiple fields
and scenarios to identify potential duplicates with detailed reasoning.

Features:
1. Multi-field duplicate analysis (invoice no, company, products, HSN, rates, amounts, dates)
2. Smart detection scenarios (exact match, partial match, near-duplicate patterns)
3. AI-powered reasoning for duplicate classification
4. Detailed reporting with evidence and recommendations
5. Integration with database and AI agent workflow
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import re
from difflib import SequenceMatcher
from decimal import Decimal

@dataclass
class DuplicateMatch:
    """Represents a potential duplicate match with evidence"""
    original_invoice_id: int
    original_invoice_num: str
    duplicate_invoice_id: int
    duplicate_invoice_num: str
    match_type: str
    confidence_score: float
    matching_fields: Dict[str, Any]
    evidence: List[str]
    recommendation: str
    database_reference: Dict[str, Any] = None  # Added for database context

@dataclass
class DuplicateAnalysisResult:
    """Complete duplicate analysis result"""
    invoice_id: int
    invoice_num: str
    is_duplicate: bool
    duplicate_matches: List[DuplicateMatch]
    analysis_summary: str
    confidence_score: float
    recommended_action: str

class IntelligentDuplicationDetector:
    """AI-powered intelligent duplication detection system"""
    
    def __init__(self, db_path: str = "invoice_management.db"):
        """Initialize the duplication detector"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Define duplication scenarios and their weights
        self.duplication_scenarios = [
            {
                "name": "Exact Invoice Number Match",
                "weight": 0.95,
                "description": "Same invoice number from same supplier"
            },
            {
                "name": "Same Invoice Content",
                "weight": 0.90,
                "description": "Same supplier, products, amounts, and nearby dates"
            },
            {
                "name": "Re-submission Pattern",
                "weight": 0.85,
                "description": "Same supplier and amounts but different invoice numbers"
            },
            {
                "name": "Product Line Duplication",
                "weight": 0.80,
                "description": "Identical product lines with same HSN codes and rates"
            },
            {
                "name": "Amount and Date Similarity",
                "weight": 0.75,
                "description": "Same amounts and very close dates from same supplier"
            },
            {
                "name": "Near-duplicate Pattern",
                "weight": 0.70,
                "description": "Similar invoice structure with minor variations"
            }
        ]
    
    def analyze_for_duplicates(self, invoice_id: int) -> DuplicateAnalysisResult:
        """Perform comprehensive duplicate analysis for an invoice"""
        print(f"🔍 INTELLIGENT DUPLICATE ANALYSIS - Invoice ID: {invoice_id}")
        print("=" * 70)
        
        # Get invoice data
        invoice_data = self._get_invoice_details(invoice_id)
        if not invoice_data:
            return DuplicateAnalysisResult(
                invoice_id=invoice_id,
                invoice_num="UNKNOWN",
                is_duplicate=False,
                duplicate_matches=[],
                analysis_summary="Invoice not found in database",
                confidence_score=0.0,
                recommended_action="VERIFY_INVOICE_EXISTS"
            )
        
        print(f"📄 Analyzing: {invoice_data['invoice_num']} from {invoice_data['supplier_name']}")
        print(f"💰 Amount: ₹{invoice_data['total_value']:,.2f}")
        print(f"📅 Date: {invoice_data['invoice_date']}")
        
        # Get all potential duplicate candidates
        candidates = self._get_duplicate_candidates(invoice_id, invoice_data)
        print(f"🎯 Found {len(candidates)} potential duplicate candidates")
        
        # Analyze each candidate
        duplicate_matches = []
        for candidate in candidates:
            match = self._analyze_candidate_match(invoice_data, candidate)
            if match and match.confidence_score > 0.5:  # Only include significant matches
                duplicate_matches.append(match)
        
        # Determine overall duplicate status
        is_duplicate = any(match.confidence_score > 0.7 for match in duplicate_matches)
        overall_confidence = max([match.confidence_score for match in duplicate_matches], default=0.0)
        
        # Generate analysis summary
        summary = self._generate_analysis_summary(invoice_data, duplicate_matches, is_duplicate)
        
        # Determine recommended action
        if is_duplicate and duplicate_matches:
            recommended_action = "MARK_AS_DUPLICATE"
        elif duplicate_matches:
            recommended_action = "MANUAL_REVIEW_REQUIRED"
        else:
            recommended_action = "APPROVE_AS_UNIQUE"
        
        result = DuplicateAnalysisResult(
            invoice_id=invoice_id,
            invoice_num=invoice_data['invoice_num'],
            is_duplicate=is_duplicate,
            duplicate_matches=duplicate_matches,
            analysis_summary=summary,
            confidence_score=overall_confidence,
            recommended_action=recommended_action
        )
        
        # Print results
        self._print_analysis_results(result)
        
        return result
    
    def _get_invoice_details(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive invoice details including line items"""
        cursor = self.conn.cursor()
        
        # Get invoice header with company info
        cursor.execute("""
            SELECT 
                i.invoice_id,
                i.invoice_num,
                i.invoice_date,
                i.taxable_value,
                i.total_tax,
                i.total_value,
                i.supplier_company_id,
                c.legal_name as supplier_name,
                c.gstin as supplier_gstin
            FROM invoices i
            LEFT JOIN companies c ON i.supplier_company_id = c.company_id
            WHERE i.invoice_id = ?
        """, (invoice_id,))
        
        invoice_row = cursor.fetchone()
        if not invoice_row:
            return None
        
        invoice_data = dict(invoice_row)
        
        # Get line items
        cursor.execute("""
            SELECT 
                ii.item_description,
                ii.hsn_code,
                ii.quantity,
                ii.unit_price,
                ii.taxable_value,
                ii.gst_rate,
                ii.total_amount,
                p.canonical_name as product_name
            FROM invoice_item ii
            LEFT JOIN products p ON ii.product_id = p.product_id
            WHERE ii.invoice_id = ?
        """, (invoice_id,))
        
        line_items = [dict(row) for row in cursor.fetchall()]
        invoice_data['line_items'] = line_items
        
        return invoice_data
    
    def _get_duplicate_candidates(self, current_invoice_id: int, invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get potential duplicate candidates based on comprehensive criteria"""
        cursor = self.conn.cursor()
        candidates = []
        
        # Scenario 1: SAME COMPANY - All invoices from same supplier (highest priority)
        print(f"   🏢 Searching same supplier invoices (Company ID: {invoice_data['supplier_company_id']})")
        cursor.execute("""
            SELECT 
                i.invoice_id,
                i.invoice_num,
                i.invoice_date,
                i.total_value,
                i.taxable_value,
                i.total_tax,
                i.supplier_company_id,
                c.legal_name as supplier_name,
                c.gstin as supplier_gstin
            FROM invoices i
            LEFT JOIN companies c ON i.supplier_company_id = c.company_id
            WHERE i.supplier_company_id = ? AND i.invoice_id != ?
            ORDER BY i.invoice_date DESC
        """, (invoice_data['supplier_company_id'], current_invoice_id))
        
        same_company_invoices = [dict(row) for row in cursor.fetchall()]
        print(f"      📊 Found {len(same_company_invoices)} invoices from same supplier")
        
        # Scenario 2: SAME INVOICE NUMBER PATTERN (across all companies)
        if invoice_data['invoice_num']:
            print(f"   📝 Searching similar invoice numbers: {invoice_data['invoice_num']}")
            # Exact match first
            cursor.execute("""
                SELECT 
                    i.invoice_id,
                    i.invoice_num,
                    i.invoice_date,
                    i.total_value,
                    i.taxable_value,
                    i.total_tax,
                    i.supplier_company_id,
                    c.legal_name as supplier_name,
                    c.gstin as supplier_gstin
                FROM invoices i
                LEFT JOIN companies c ON i.supplier_company_id = c.company_id
                WHERE i.invoice_num = ? AND i.invoice_id != ?
            """, (invoice_data['invoice_num'], current_invoice_id))
            
            exact_invoice_matches = [dict(row) for row in cursor.fetchall()]
            print(f"      📊 Found {len(exact_invoice_matches)} exact invoice number matches")
        else:
            exact_invoice_matches = []
        
        # Scenario 3: SIMILAR AMOUNTS (within 1% variance)
        total_value = invoice_data.get('total_value', 0)
        if total_value is None:
            total_value = 0
        try:
            total_value = float(total_value)
        except (ValueError, TypeError):
            total_value = 0
            
        amount_variance = total_value * 0.01
        print(f"   💰 Searching similar amounts: ₹{total_value:,.2f} (±₹{amount_variance:.2f})")
        cursor.execute("""
            SELECT 
                i.invoice_id,
                i.invoice_num,
                i.invoice_date,
                i.total_value,
                i.taxable_value,
                i.total_tax,
                i.supplier_company_id,
                c.legal_name as supplier_name,
                c.gstin as supplier_gstin
            FROM invoices i
            LEFT JOIN companies c ON i.supplier_company_id = c.company_id
            WHERE i.total_value BETWEEN ? AND ? 
            AND i.invoice_id != ?
            ORDER BY ABS(i.total_value - ?) ASC
            LIMIT 10
        """, (
            total_value - amount_variance,
            total_value + amount_variance,
            current_invoice_id,
            total_value
        ))
        
        similar_amount_invoices = [dict(row) for row in cursor.fetchall()]
        print(f"      📊 Found {len(similar_amount_invoices)} invoices with similar amounts")
        
        # Scenario 4: PRODUCT-BASED MATCHING (same HSN codes from any supplier)
        print(f"   🔍 Searching product matches by HSN codes...")
        current_hsn_codes = []
        cursor.execute("""
            SELECT DISTINCT hsn_code FROM invoice_item 
            WHERE invoice_id = ? AND hsn_code IS NOT NULL
        """, (current_invoice_id,))
        current_hsn_codes = [row[0] for row in cursor.fetchall()]
        
        product_match_invoices = []
        if current_hsn_codes:
            placeholders = ','.join(['?' for _ in current_hsn_codes])
            cursor.execute(f"""
                SELECT DISTINCT
                    i.invoice_id,
                    i.invoice_num,
                    i.invoice_date,
                    i.total_value,
                    i.taxable_value,
                    i.total_tax,
                    i.supplier_company_id,
                    c.legal_name as supplier_name,
                    c.gstin as supplier_gstin,
                    COUNT(DISTINCT ii.hsn_code) as matching_hsn_count
                FROM invoices i
                LEFT JOIN companies c ON i.supplier_company_id = c.company_id
                JOIN invoice_item ii ON i.invoice_id = ii.invoice_id
                WHERE ii.hsn_code IN ({placeholders}) 
                AND i.invoice_id != ?
                GROUP BY i.invoice_id
                HAVING matching_hsn_count >= 1
                ORDER BY matching_hsn_count DESC
                LIMIT 10
            """, (*current_hsn_codes, current_invoice_id))
            
            product_match_invoices = [dict(row) for row in cursor.fetchall()]
            print(f"      📊 Found {len(product_match_invoices)} invoices with matching HSN codes: {current_hsn_codes}")
        
        # Combine and deduplicate candidates
        all_candidates = (same_company_invoices + exact_invoice_matches + 
                         similar_amount_invoices + product_match_invoices)
        seen_ids = set()
        
        for candidate in all_candidates:
            if candidate['invoice_id'] not in seen_ids:
                # Get complete invoice details including line items
                candidate_details = self._get_invoice_details(candidate['invoice_id'])
                if candidate_details:
                    candidates.append(candidate_details)
                    seen_ids.add(candidate['invoice_id'])
        
        print(f"   📈 Total unique candidates for analysis: {len(candidates)}")
        return candidates
    
    def _analyze_candidate_match(self, current_invoice: Dict, candidate: Dict) -> Optional[DuplicateMatch]:
        """Analyze if a candidate is a duplicate of the current invoice"""
        matching_fields = {}
        evidence = []
        confidence_score = 0.0
        match_type = "NO_MATCH"
        
        # 1. HIGHEST PRIORITY: Same Invoice Number + Same Company (95% confidence)
        if (current_invoice['invoice_num'] and candidate['invoice_num'] and
            current_invoice['invoice_num'].strip().upper() == candidate['invoice_num'].strip().upper()):
            
            if current_invoice['supplier_company_id'] == candidate['supplier_company_id']:
                confidence_score = 0.95
                match_type = "EXACT_INVOICE_NUMBER_SAME_COMPANY"
                matching_fields['invoice_number'] = current_invoice['invoice_num']
                matching_fields['supplier_company_id'] = current_invoice['supplier_company_id']
                evidence.append(f"Exact invoice number match: {current_invoice['invoice_num']}")
                evidence.append(f"Same supplier company ID: {current_invoice['supplier_company_id']}")
                evidence.append(f"Same supplier: {current_invoice['supplier_name']}")
        
        # 2. PRODUCT-LEVEL DUPLICATION: Same Company + Same Product Details (90% confidence)
        elif current_invoice['supplier_company_id'] == candidate['supplier_company_id']:
            product_match_score = self._analyze_product_line_duplication(
                current_invoice.get('line_items', []),
                candidate.get('line_items', [])
            )
            
            if product_match_score['similarity_score'] >= 0.85:  # 85% product similarity threshold
                confidence_score = 0.90 * product_match_score['similarity_score']
                match_type = "SAME_COMPANY_PRODUCT_DUPLICATION"
                matching_fields.update({
                    'supplier_company_id': current_invoice['supplier_company_id'],
                    'product_similarity': product_match_score['similarity_score'],
                    'matching_products': product_match_score['matching_count'],
                    'matching_hsn_codes': product_match_score['matching_hsn_codes']
                })
                evidence.append(f"Same supplier company: {current_invoice['supplier_name']}")
                evidence.append(f"Product similarity: {product_match_score['similarity_score']:.1%}")
                evidence.append(f"Matching products: {product_match_score['matching_count']} out of {len(current_invoice.get('line_items', []))}")
                if product_match_score['matching_hsn_codes']:
                    evidence.append(f"Matching HSN codes: {', '.join(product_match_score['matching_hsn_codes'])}")
        
        # 3. AMOUNT + DATE PATTERN: Same Supplier + Amount + Close Date (85% confidence)
        elif (current_invoice['supplier_company_id'] == candidate['supplier_company_id'] and
              self._safe_numeric_difference(current_invoice['total_value'], candidate['total_value']) < 0.01):
            
            date_diff = self._calculate_date_difference(
                current_invoice['invoice_date'], 
                candidate['invoice_date']
            )
            
            if date_diff is not None and date_diff <= 7:  # Within 7 days
                base_confidence = 0.85
                # Reduce confidence based on date difference
                confidence_score = base_confidence - (date_diff * 0.03)
                match_type = "SAME_SUPPLIER_AMOUNT_DATE"
                
                matching_fields.update({
                    'supplier_company_id': current_invoice['supplier_company_id'],
                    'supplier': current_invoice['supplier_name'],
                    'total_amount': current_invoice['total_value'],
                    'date_difference_days': date_diff
                })
                evidence.append(f"Same supplier: {current_invoice['supplier_name']}")
                evidence.append(f"Identical amount: ₹{current_invoice['total_value']:,.2f}")
                evidence.append(f"Close dates: {date_diff} days apart")
        
        # 3. Product Line Analysis (80-85% confidence)
        line_item_similarity = self._analyze_line_item_similarity(
            current_invoice.get('line_items', []),
            candidate.get('line_items', [])
        )
        
        if line_item_similarity['similarity_score'] > 0.8:
            if confidence_score < 0.85:
                confidence_score = 0.80 + (line_item_similarity['similarity_score'] * 0.05)
                match_type = "PRODUCT_LINE_DUPLICATION"
                
                matching_fields.update({
                    'line_item_similarity': line_item_similarity['similarity_score'],
                    'matching_products': line_item_similarity['matching_items']
                })
                
                evidence.append(f"High product similarity: {line_item_similarity['similarity_score']:.1%}")
                evidence.extend(line_item_similarity['evidence'])
        
        # 4. HSN Code Pattern Match (75% confidence)
        hsn_similarity = self._analyze_hsn_similarity(
            current_invoice.get('line_items', []),
            candidate.get('line_items', [])
        )
        
        if hsn_similarity['match_ratio'] > 0.8 and confidence_score < 0.75:
            confidence_score = max(confidence_score, 0.70 + (hsn_similarity['match_ratio'] * 0.05))
            
            if match_type == "NO_MATCH":
                match_type = "HSN_PATTERN_MATCH"
            
            matching_fields.update({
                'hsn_similarity': hsn_similarity['match_ratio'],
                'matching_hsn_codes': hsn_similarity['matching_hsn']
            })
            
            evidence.append(f"HSN code similarity: {hsn_similarity['match_ratio']:.1%}")
            evidence.extend(hsn_similarity['evidence'])
        
        # 5. Rate and Quantity Similarity (70% confidence)
        rate_similarity = self._analyze_rate_similarity(
            current_invoice.get('line_items', []),
            candidate.get('line_items', [])
        )
        
        if rate_similarity['similarity_score'] > 0.85 and confidence_score < 0.70:
            confidence_score = max(confidence_score, 0.65 + (rate_similarity['similarity_score'] * 0.05))
            
            if match_type == "NO_MATCH":
                match_type = "RATE_PATTERN_MATCH"
            
            matching_fields.update({
                'rate_similarity': rate_similarity['similarity_score'],
                'matching_rates': rate_similarity['matching_rates']
            })
            
            evidence.append(f"Rate similarity: {rate_similarity['similarity_score']:.1%}")
            evidence.extend(rate_similarity['evidence'])
        
        # Generate recommendation based on confidence
        if confidence_score >= 0.85:
            recommendation = "HIGH_CONFIDENCE_DUPLICATE"
        elif confidence_score >= 0.70:
            recommendation = "LIKELY_DUPLICATE_REVIEW_REQUIRED"
        elif confidence_score >= 0.50:
            recommendation = "POSSIBLE_DUPLICATE_INVESTIGATE"
        else:
            recommendation = "NOT_A_DUPLICATE"
        
        if confidence_score > 0.5:
            return DuplicateMatch(
                original_invoice_id=candidate['invoice_id'],
                original_invoice_num=candidate['invoice_num'],
                duplicate_invoice_id=current_invoice['invoice_id'],
                duplicate_invoice_num=current_invoice['invoice_num'],
                match_type=match_type,
                confidence_score=confidence_score,
                matching_fields=matching_fields,
                evidence=evidence,
                recommendation=recommendation,
                database_reference={
                    "original_invoice": {
                        "table": "invoices",
                        "invoice_id": candidate['invoice_id'],
                        "stored_values": {
                            "invoice_num": candidate['invoice_num'],
                            "invoice_date": candidate['invoice_date'],
                            "total_value": candidate['total_value'],
                            "supplier_name": candidate['supplier_name'],
                            "supplier_company_id": candidate['supplier_company_id']
                        }
                    },
                    "current_invoice": {
                        "table": "invoices", 
                        "invoice_id": current_invoice['invoice_id'],
                        "stored_values": {
                            "invoice_num": current_invoice['invoice_num'],
                            "invoice_date": current_invoice['invoice_date'], 
                            "total_value": current_invoice['total_value'],
                            "supplier_name": current_invoice['supplier_name'],
                            "supplier_company_id": current_invoice['supplier_company_id']
                        }
                    },
                    "comparison_details": matching_fields
                }
            )
        
        return None
    
    def _analyze_product_line_duplication(self, current_items: List[Dict], candidate_items: List[Dict]) -> Dict[str, Any]:
        """Analyze product-level duplication between two invoices"""
        if not current_items or not candidate_items:
            return {'similarity_score': 0.0, 'matching_count': 0, 'matching_hsn_codes': []}
        
        matching_count = 0
        matching_hsn_codes = set()
        total_similarity = 0.0
        detailed_matches = []
        
        for curr_item in current_items:
            best_match_score = 0.0
            best_match = None
            
            for cand_item in candidate_items:
                item_similarity = self._calculate_item_similarity(curr_item, cand_item)
                if item_similarity > best_match_score:
                    best_match_score = item_similarity
                    best_match = cand_item
            
            # Consider it a match if similarity > 80%
            if best_match_score > 0.80:
                matching_count += 1
                total_similarity += best_match_score
                
                # Track matching HSN codes
                if curr_item.get('hsn_code') == best_match.get('hsn_code'):
                    matching_hsn_codes.add(curr_item.get('hsn_code'))
                
                detailed_matches.append({
                    'current_item': {
                        'description': curr_item.get('item_description', ''),
                        'hsn_code': curr_item.get('hsn_code', ''),
                        'unit_price': curr_item.get('unit_price', 0),
                        'taxable_value': curr_item.get('taxable_value', 0)
                    },
                    'matched_item': {
                        'description': best_match.get('item_description', ''),
                        'hsn_code': best_match.get('hsn_code', ''),
                        'unit_price': best_match.get('unit_price', 0),
                        'taxable_value': best_match.get('taxable_value', 0)
                    },
                    'similarity_score': best_match_score
                })
        
        # Calculate overall similarity
        if matching_count > 0:
            avg_similarity = total_similarity / matching_count
            # Weight by percentage of items matched
            coverage_factor = matching_count / len(current_items)
            overall_similarity = avg_similarity * coverage_factor
        else:
            overall_similarity = 0.0
        
        return {
            'similarity_score': overall_similarity,
            'matching_count': matching_count,
            'total_items': len(current_items),
            'matching_hsn_codes': list(matching_hsn_codes),
            'detailed_matches': detailed_matches
        }
    
    def _calculate_item_similarity(self, item1: Dict, item2: Dict) -> float:
        """Calculate similarity between two line items"""
        similarity_factors = []
        
        # 1. Description similarity (40% weight)
        desc1 = str(item1.get('item_description', '')).lower().strip()
        desc2 = str(item2.get('item_description', '')).lower().strip()
        if desc1 and desc2:
            desc_similarity = self._text_similarity(desc1, desc2)
            similarity_factors.append(('description', desc_similarity, 0.40))
        
        # 2. HSN code exact match (25% weight)
        hsn1 = str(item1.get('hsn_code', '')).strip()
        hsn2 = str(item2.get('hsn_code', '')).strip()
        if hsn1 and hsn2:
            hsn_match = 1.0 if hsn1 == hsn2 else 0.0
            similarity_factors.append(('hsn_code', hsn_match, 0.25))
        
        # 3. Unit price similarity (20% weight)
        try:
            price1 = float(item1.get('unit_price', 0)) if item1.get('unit_price') is not None else 0
            price2 = float(item2.get('unit_price', 0)) if item2.get('unit_price') is not None else 0
            if price1 > 0 and price2 > 0:
                price_similarity = 1.0 - abs(price1 - price2) / max(price1, price2)
                if price_similarity < 0:
                    price_similarity = 0.0
                similarity_factors.append(('unit_price', price_similarity, 0.20))
        except (ValueError, TypeError):
            # Skip price similarity if values can't be converted
            pass
        
        # 4. Taxable value similarity (15% weight)
        try:
            value1 = float(item1.get('taxable_value', 0)) if item1.get('taxable_value') is not None else 0
            value2 = float(item2.get('taxable_value', 0)) if item2.get('taxable_value') is not None else 0
            if value1 > 0 and value2 > 0:
                value_similarity = 1.0 - abs(value1 - value2) / max(value1, value2)
                if value_similarity < 0:
                    value_similarity = 0.0
                similarity_factors.append(('taxable_value', value_similarity, 0.15))
        except (ValueError, TypeError):
            # Skip taxable value similarity if values can't be converted
            pass
        if value1 > 0 and value2 > 0:
            value_similarity = 1.0 - abs(value1 - value2) / max(value1, value2)
            if value_similarity < 0:
                value_similarity = 0.0
            similarity_factors.append(('taxable_value', value_similarity, 0.15))
        
        # Calculate weighted average
        if not similarity_factors:
            return 0.0
        
        total_weight = sum(weight for _, _, weight in similarity_factors)
        weighted_score = sum(score * weight for _, score, weight in similarity_factors)
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _analyze_line_item_similarity(self, items1: List[Dict], items2: List[Dict]) -> Dict[str, Any]:
        """Analyze similarity between line items of two invoices"""
        if not items1 or not items2:
            return {'similarity_score': 0.0, 'matching_items': [], 'evidence': []}
        
        matching_items = []
        evidence = []
        total_matches = 0
        
        for item1 in items1:
            best_match_score = 0.0
            best_match_item = None
            
            for item2 in items2:
                # Calculate similarity based on description, HSN, quantity, and rate
                desc_similarity = self._text_similarity(
                    str(item1.get('item_description', '')).lower(),
                    str(item2.get('item_description', '')).lower()
                )
                
                hsn_match = 1.0 if item1.get('hsn_code') == item2.get('hsn_code') else 0.0
                
                # Quantity and rate similarity (within 5% variance)
                qty_similarity = self._numeric_similarity(
                    item1.get('quantity', 0), 
                    item2.get('quantity', 0)
                )
                
                rate_similarity = self._numeric_similarity(
                    item1.get('unit_price', 0), 
                    item2.get('unit_price', 0)
                )
                
                # Overall item similarity
                item_similarity = (desc_similarity * 0.3 + hsn_match * 0.3 + 
                                 qty_similarity * 0.2 + rate_similarity * 0.2)
                
                if item_similarity > best_match_score:
                    best_match_score = item_similarity
                    best_match_item = item2
            
            if best_match_score > 0.7:  # Consider it a match
                matching_items.append({
                    'item1': item1.get('item_description'),
                    'item2': best_match_item.get('item_description'),
                    'similarity': best_match_score,
                    'hsn_code': item1.get('hsn_code')
                })
                
                evidence.append(
                    f"Product match: {item1.get('item_description')} "
                    f"(HSN: {item1.get('hsn_code')}, "
                    f"Rate: ₹{item1.get('unit_price', 0):,.2f})"
                )
                
                total_matches += best_match_score
        
        similarity_score = total_matches / max(len(items1), len(items2)) if items1 or items2 else 0.0
        
        return {
            'similarity_score': similarity_score,
            'matching_items': matching_items,
            'evidence': evidence
        }
    
    def _analyze_hsn_similarity(self, items1: List[Dict], items2: List[Dict]) -> Dict[str, Any]:
        """Analyze HSN code similarity between invoices"""
        if not items1 or not items2:
            return {'match_ratio': 0.0, 'matching_hsn': [], 'evidence': []}
        
        hsn1 = set(item.get('hsn_code') for item in items1 if item.get('hsn_code'))
        hsn2 = set(item.get('hsn_code') for item in items2 if item.get('hsn_code'))
        
        if not hsn1 or not hsn2:
            return {'match_ratio': 0.0, 'matching_hsn': [], 'evidence': []}
        
        matching_hsn = hsn1.intersection(hsn2)
        match_ratio = len(matching_hsn) / len(hsn1.union(hsn2))
        
        evidence = []
        if matching_hsn:
            evidence.append(f"Matching HSN codes: {', '.join(matching_hsn)}")
        
        return {
            'match_ratio': match_ratio,
            'matching_hsn': list(matching_hsn),
            'evidence': evidence
        }
    
    def _analyze_rate_similarity(self, items1: List[Dict], items2: List[Dict]) -> Dict[str, Any]:
        """Analyze rate and quantity similarity between invoices"""
        if not items1 or not items2:
            return {'similarity_score': 0.0, 'matching_rates': [], 'evidence': []}
        
        rates1 = [(item.get('unit_price', 0), item.get('quantity', 0)) for item in items1]
        rates2 = [(item.get('unit_price', 0), item.get('quantity', 0)) for item in items2]
        
        matching_rates = []
        evidence = []
        total_similarity = 0.0
        
        for rate1, qty1 in rates1:
            best_similarity = 0.0
            best_match = None
            
            for rate2, qty2 in rates2:
                rate_sim = self._numeric_similarity(rate1, rate2)
                qty_sim = self._numeric_similarity(qty1, qty2)
                combined_sim = (rate_sim + qty_sim) / 2
                
                if combined_sim > best_similarity:
                    best_similarity = combined_sim
                    best_match = (rate2, qty2)
            
            if best_similarity > 0.8:
                matching_rates.append({
                    'rate1': rate1, 'qty1': qty1,
                    'rate2': best_match[0], 'qty2': best_match[1],
                    'similarity': best_similarity
                })
                
                evidence.append(f"Similar rate/qty: ₹{rate1:,.2f} x {qty1}")
                total_similarity += best_similarity
        
        similarity_score = total_similarity / max(len(rates1), len(rates2)) if rates1 or rates2 else 0.0
        
        return {
            'similarity_score': similarity_score,
            'matching_rates': matching_rates,
            'evidence': evidence
        }
    
    def _safe_numeric_difference(self, num1, num2) -> float:
        """Safely calculate the difference between two numbers, handling None values"""
        try:
            n1 = float(num1) if num1 is not None else 0
            n2 = float(num2) if num2 is not None else 0
            return abs(n1 - n2)
        except (ValueError, TypeError):
            return float('inf')  # Return a large number if conversion fails

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using SequenceMatcher"""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _numeric_similarity(self, num1: float, num2: float, tolerance: float = 0.05) -> float:
        """Calculate numeric similarity within tolerance"""
        # Handle None values
        if num1 is None or num2 is None:
            return 0.0
            
        # Convert to float if needed
        try:
            num1 = float(num1)
            num2 = float(num2)
        except (ValueError, TypeError):
            return 0.0
            
        if num1 == 0 and num2 == 0:
            return 1.0
        
        if num1 == 0 or num2 == 0:
            return 0.0
        
        diff_ratio = abs(num1 - num2) / max(abs(num1), abs(num2))
        
        if diff_ratio <= tolerance:
            return 1.0 - (diff_ratio / tolerance)
        else:
            return 0.0
    
    def _calculate_date_difference(self, date1: str, date2: str) -> Optional[int]:
        """Calculate difference between two dates in days"""
        try:
            if not date1 or not date2:
                return None
            
            # Parse dates (assuming YYYY-MM-DD format)
            d1 = datetime.strptime(date1, "%Y-%m-%d").date()
            d2 = datetime.strptime(date2, "%Y-%m-%d").date()
            
            return abs((d1 - d2).days)
        except:
            return None
    
    def _generate_analysis_summary(self, invoice_data: Dict, matches: List[DuplicateMatch], is_duplicate: bool) -> str:
        """Generate comprehensive analysis summary"""
        summary_parts = []
        
        summary_parts.append(f"Invoice Analysis: {invoice_data['invoice_num']}")
        summary_parts.append(f"Supplier: {invoice_data['supplier_name']}")
        summary_parts.append(f"Amount: ₹{invoice_data['total_value']:,.2f}")
        
        if matches:
            summary_parts.append(f"\nFound {len(matches)} potential duplicate(s):")
            
            for i, match in enumerate(matches, 1):
                summary_parts.append(
                    f"{i}. {match.original_invoice_num} "
                    f"(Confidence: {match.confidence_score:.1%}, "
                    f"Type: {match.match_type})"
                )
        else:
            summary_parts.append("\nNo significant duplicate patterns detected.")
        
        if is_duplicate:
            summary_parts.append("\n🚨 CONCLUSION: This invoice appears to be a DUPLICATE.")
        else:
            summary_parts.append("\n✅ CONCLUSION: This invoice appears to be UNIQUE.")
        
        return "\n".join(summary_parts)
    
    def _print_analysis_results(self, result: DuplicateAnalysisResult):
        """Print formatted analysis results"""
        print(f"\n📊 DUPLICATE ANALYSIS RESULTS:")
        print("-" * 70)
        
        status = "🚨 DUPLICATE DETECTED" if result.is_duplicate else "✅ UNIQUE INVOICE"
        print(f"Status: {status}")
        print(f"Confidence: {result.confidence_score:.1%}")
        print(f"Recommendation: {result.recommended_action}")
        
        # Add detailed reasoning for the result
        if result.is_duplicate:
            print(f"\n🔍 DUPLICATION REASONS:")
            duplicate_count = len(result.duplicate_matches)
            print(f"   • Found {duplicate_count} potential duplicate{'s' if duplicate_count != 1 else ''}")
            
            # Summarize match types
            match_types = [match.match_type for match in result.duplicate_matches]
            unique_match_types = list(set(match_types))
            print(f"   • Match types detected: {', '.join(unique_match_types)}")
            
            # High confidence matches
            high_conf_matches = [m for m in result.duplicate_matches if m.confidence_score >= 0.85]
            if high_conf_matches:
                print(f"   • {len(high_conf_matches)} high-confidence match{'es' if len(high_conf_matches) != 1 else ''} found")
            
            # Common fields
            all_fields = set()
            for match in result.duplicate_matches:
                all_fields.update(match.matching_fields.keys())
            if all_fields:
                print(f"   • Common duplicate indicators: {', '.join(list(all_fields)[:5])}")
        else:
            print(f"\n✅ UNIQUENESS REASONS:")
            print(f"   • No significant duplicate patterns detected across all comparison criteria")
            print(f"   • Invoice number, supplier, amount, and date combinations are unique")
            print(f"   • Product/service details don't match existing invoices significantly")
            print(f"   • All business identifiers (GSTIN, amounts, dates) are distinct")
            if result.confidence_score == 0.0:
                print(f"   • This appears to be the first invoice from this supplier or with these characteristics")
        
        if result.duplicate_matches:
            print(f"\n🔍 POTENTIAL DUPLICATES ({len(result.duplicate_matches)}):")
            print("-" * 50)
            
            for i, match in enumerate(result.duplicate_matches, 1):
                print(f"\n{i}. Original Invoice: {match.original_invoice_num}")
                print(f"   Match Type: {match.match_type}")
                print(f"   Confidence: {match.confidence_score:.1%}")
                print(f"   Recommendation: {match.recommendation}")
                
                print(f"   Matching Fields:")
                for field, value in match.matching_fields.items():
                    print(f"     • {field}: {value}")
                
                if match.evidence:
                    print(f"   Evidence:")
                    for evidence in match.evidence:
                        print(f"     • {evidence}")
                
                # Show detailed database reference for duplicates
                if match.database_reference:
                    db_ref = match.database_reference
                    print(f"   📊 Database Reference:")
                    
                    if 'original_invoice' in db_ref:
                        orig = db_ref['original_invoice']
                        print(f"      Original Invoice (ID: {orig['invoice_id']}):")
                        print(f"         Table: {orig['table']}")
                        print(f"         Values: {orig['stored_values']}")
                    
                    if 'current_invoice' in db_ref:
                        curr = db_ref['current_invoice'] 
                        print(f"      Current Invoice (ID: {curr['invoice_id']}):")
                        print(f"         Table: {curr['table']}")
                        print(f"         Values: {curr['stored_values']}")
                    
                    if 'comparison_details' in db_ref:
                        print(f"      Comparison Details: {db_ref['comparison_details']}")
        
        print(f"\n📝 Summary:")
        print(result.analysis_summary)
        
        # Add conclusion with actionable recommendations
        if result.is_duplicate:
            print(f"\n🚨 CONCLUSION: This invoice has potential duplicates.")
            print(f"   Action Required: Review {len(result.duplicate_matches)} matching invoice{'s' if len(result.duplicate_matches) != 1 else ''}")
        else:
            print(f"\n✅ CONCLUSION: This invoice appears to be UNIQUE.")
            print(f"   Action: APPROVE_AS_UNIQUE - Safe to process")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main function for testing intelligent duplicate detection"""
    print("🤖 INTELLIGENT DUPLICATION DETECTION SYSTEM")
    print("=" * 70)
    
    detector = IntelligentDuplicationDetector()
    
    # Test with existing invoices
    cursor = detector.conn.cursor()
    cursor.execute("SELECT invoice_id, invoice_num FROM invoices ORDER BY invoice_id")
    invoices = cursor.fetchall()
    
    if not invoices:
        print("⚠️  No invoices found in database.")
        return
    
    print(f"📋 Found {len(invoices)} invoices in database:")
    for invoice in invoices:
        print(f"  - Invoice ID {invoice[0]}: {invoice[1]}")
    
    # Analyze each invoice
    for invoice_id, invoice_num in invoices:
        print(f"\n" + "=" * 70)
        result = detector.analyze_for_duplicates(invoice_id)
    
    detector.close()

if __name__ == "__main__":
    main()