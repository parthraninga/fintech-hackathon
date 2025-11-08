#!/usr/bin/env python3
"""
Simplified but Powerful Financial Chatbot
This version uses your existing database infrastructure without complex LangChain dependencies
"""

import sys
import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Optional

# Import your existing database services
from invoice_database import InvoiceDatabase
from gst_service import GSTService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplePowerfulFinancialChatbot:
    """Advanced financial chatbot using existing database infrastructure"""
    
    def __init__(self, db_path: str = "invoice_management.db"):
        """Initialize the chatbot with database connections"""
        self.db = InvoiceDatabase(db_path)
        self.gst_service = GSTService(db_path)
        logger.info("✅ Financial chatbot initialized successfully")
    
    def chat(self, message: str, session_id: str = None) -> str:
        """Process a chat message and return response"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"📝 Processing query: '{message}' for session: {session_id}")
        
        try:
            # Classify the query type
            query_type = self._classify_query(message.lower())
            
            # Get database results
            results = self._get_database_results(message, query_type)
            
            # Generate human-readable response
            response = self._generate_response(message, query_type, results)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error processing query: {str(e)}")
            return f"I encountered an issue processing your request: {str(e)}. Please try a simpler question."
    
    def _classify_query(self, query: str) -> str:
        """Classify the user query type"""
        if any(word in query for word in ["invoice", "bill", "receipt"]):
            return "invoice_query"
        elif any(word in query for word in ["company", "supplier", "buyer", "gstin", "gst"]):
            return "company_query"
        elif any(word in query for word in ["product", "hsn", "item"]):
            return "product_query"
        elif any(word in query for word in ["total", "sum", "amount", "analysis", "report"]):
            return "financial_analysis"
        elif any(word in query for word in ["validate", "check", "verify"]):
            return "validation_query"
        elif any(word in query for word in ["payment", "paid", "due", "outstanding"]):
            return "payment_query"
        else:
            return "general_query"
    
    def _get_database_results(self, query: str, query_type: str) -> Dict[str, Any]:
        """Get relevant data from database"""
        conn = self.db.conn
        cursor = conn.cursor()
        
        try:
            if query_type == "invoice_query":
                return self._search_invoices(cursor, query)
            elif query_type == "company_query":
                return self._search_companies(cursor, query)
            elif query_type == "product_query":
                return self._search_products(cursor, query)
            elif query_type == "financial_analysis":
                return self._perform_financial_analysis(cursor, query)
            elif query_type == "validation_query":
                return self._perform_validation(cursor, query)
            elif query_type == "payment_query":
                return self._search_payments(cursor, query)
            else:
                return self._get_general_info(cursor)
                
        except Exception as e:
            return {"error": str(e)}
    
    def _search_invoices(self, cursor, query: str) -> Dict[str, Any]:
        """Search invoices with detailed information"""
        sql_query = """
        SELECT 
            i.invoice_id, i.invoice_num, i.invoice_date,
            i.supplier_name, i.buyer_name,
            i.taxable_value, i.total_tax, i.total_value,
            i.status, i.validation, i.duplication
        FROM invoices i
        ORDER BY i.invoice_date DESC
        LIMIT 10
        """
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        formatted_results = []
        for row in results:
            formatted_results.append({
                "invoice_id": row[0],
                "invoice_number": row[1],
                "date": row[2],
                "supplier": row[3],
                "buyer": row[4],
                "taxable_value": float(row[5]) if row[5] else 0,
                "tax_amount": float(row[6]) if row[6] else 0,
                "total_value": float(row[7]) if row[7] else 0,
                "status": row[8],
                "validated": bool(row[9]),
                "duplicate": bool(row[10])
            })
        
        return {
            "type": "invoice_search",
            "results": formatted_results,
            "count": len(formatted_results)
        }
    
    def _search_companies(self, cursor, query: str) -> Dict[str, Any]:
        """Search companies with GST information"""
        sql_query = """
        SELECT 
            c.company_id, c.legal_name, c.gstin, c.city, c.state,
            g.status as gst_status, g.constitution, g.nature_of_business
        FROM companies c
        LEFT JOIN gst_companies g ON c.gstin = g.gstin
        ORDER BY c.legal_name
        LIMIT 15
        """
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        formatted_results = []
        for row in results:
            formatted_results.append({
                "company_id": row[0],
                "name": row[1],
                "gstin": row[2],
                "city": row[3],
                "state": row[4],
                "gst_status": row[5],
                "constitution": row[6],
                "business_nature": row[7]
            })
        
        return {
            "type": "company_search",
            "results": formatted_results,
            "count": len(formatted_results)
        }
    
    def _search_products(self, cursor, query: str) -> Dict[str, Any]:
        """Search products by name or HSN code"""
        sql_query = """
        SELECT 
            product_id, canonical_name, hsn_code, 
            default_tax_rate, description, unit_of_measure
        FROM products
        ORDER BY canonical_name
        LIMIT 15
        """
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        formatted_results = []
        for row in results:
            formatted_results.append({
                "product_id": row[0],
                "name": row[1],
                "hsn_code": row[2],
                "tax_rate": float(row[3]),
                "description": row[4],
                "unit": row[5]
            })
        
        return {
            "type": "product_search",
            "results": formatted_results,
            "count": len(formatted_results)
        }
    
    def _perform_financial_analysis(self, cursor, query: str) -> Dict[str, Any]:
        """Perform comprehensive financial analysis"""
        # Total invoices and amounts
        cursor.execute("""
        SELECT 
            COUNT(*) as total_invoices,
            SUM(taxable_value) as total_taxable,
            SUM(total_tax) as total_tax,
            SUM(total_value) as total_amount
        FROM invoices
        """)
        
        totals = cursor.fetchone()
        
        # Monthly trends
        cursor.execute("""
        SELECT 
            strftime('%Y-%m', invoice_date) as month,
            COUNT(*) as invoice_count,
            SUM(total_value) as monthly_total
        FROM invoices
        WHERE invoice_date >= date('now', '-12 months')
        GROUP BY strftime('%Y-%m', invoice_date)
        ORDER BY month DESC
        """)
        
        monthly_data = cursor.fetchall()
        
        # Top suppliers
        cursor.execute("""
        SELECT 
            supplier_name,
            COUNT(*) as invoice_count,
            SUM(total_value) as total_amount
        FROM invoices
        GROUP BY supplier_name
        ORDER BY total_amount DESC
        LIMIT 10
        """)
        
        top_suppliers = cursor.fetchall()
        
        return {
            "type": "financial_analysis",
            "summary": {
                "total_invoices": totals[0] if totals[0] else 0,
                "total_taxable": float(totals[1]) if totals[1] else 0,
                "total_tax": float(totals[2]) if totals[2] else 0,
                "total_amount": float(totals[3]) if totals[3] else 0
            },
            "monthly_trends": [
                {
                    "month": row[0],
                    "invoice_count": row[1],
                    "total_amount": float(row[2]) if row[2] else 0
                }
                for row in monthly_data
            ],
            "top_suppliers": [
                {
                    "name": row[0],
                    "invoice_count": row[1],
                    "total_amount": float(row[2]) if row[2] else 0
                }
                for row in top_suppliers
            ]
        }
    
    def _perform_validation(self, cursor, query: str) -> Dict[str, Any]:
        """Perform validation checks"""
        return {
            "type": "validation",
            "message": "Validation features available. Please specify what you'd like to validate (GSTIN, invoice numbers, etc.)"
        }
    
    def _search_payments(self, cursor, query: str) -> Dict[str, Any]:
        """Search payment information"""
        cursor.execute("""
        SELECT 
            p.payment_id, p.payment_date, p.amount, p.status,
            i.invoice_num, i.total_value
        FROM payment p
        JOIN invoices i ON p.invoice_id = i.invoice_id
        ORDER BY p.payment_date DESC
        LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        formatted_results = []
        for row in results:
            formatted_results.append({
                "payment_id": row[0],
                "date": row[1],
                "amount": float(row[2]) if row[2] else 0,
                "status": row[3],
                "invoice_number": row[4],
                "invoice_total": float(row[5]) if row[5] else 0
            })
        
        return {
            "type": "payment_search",
            "results": formatted_results,
            "count": len(formatted_results)
        }
    
    def _get_general_info(self, cursor) -> Dict[str, Any]:
        """Get general database information"""
        cursor.execute("SELECT COUNT(*) FROM invoices")
        invoice_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM companies")
        company_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        return {
            "type": "general_info",
            "database_stats": {
                "invoices": invoice_count,
                "companies": company_count,
                "products": product_count
            }
        }
    
    def _generate_response(self, query: str, query_type: str, results: Dict[str, Any]) -> str:
        """Generate human-readable response from database results"""
        
        if "error" in results:
            return f"❌ I encountered an error: {results['error']}"
        
        if query_type == "invoice_query":
            return self._format_invoice_response(results)
        elif query_type == "company_query":
            return self._format_company_response(results)
        elif query_type == "product_query":
            return self._format_product_response(results)
        elif query_type == "financial_analysis":
            return self._format_financial_analysis_response(results)
        elif query_type == "payment_query":
            return self._format_payment_response(results)
        else:
            return self._format_general_response(results)
    
    def _format_invoice_response(self, results: Dict[str, Any]) -> str:
        """Format invoice search results"""
        if not results.get("results"):
            return "📄 No invoices found in the database."
        
        response = f"📄 **Invoice Search Results ({results['count']} found):**\n\n"
        
        for invoice in results["results"][:5]:  # Show top 5
            response += f"🧾 **Invoice #{invoice['invoice_number']}**\n"
            response += f"   📅 Date: {invoice['date']}\n"
            response += f"   🏢 Supplier: {invoice['supplier']}\n"
            response += f"   🏬 Buyer: {invoice['buyer']}\n"
            response += f"   💰 Total: ₹{invoice['total_value']:,.2f}\n"
            response += f"   📊 Status: {invoice['status']}\n\n"
        
        if results["count"] > 5:
            response += f"... and {results['count'] - 5} more invoices.\n"
        
        return response
    
    def _format_company_response(self, results: Dict[str, Any]) -> str:
        """Format company search results"""
        if not results.get("results"):
            return "🏢 No companies found in the database."
        
        response = f"🏢 **Company Search Results ({results['count']} found):**\n\n"
        
        for company in results["results"][:5]:
            response += f"🏢 **{company['name']}**\n"
            response += f"   🆔 GSTIN: {company['gstin']}\n"
            response += f"   📍 Location: {company['city']}, {company['state']}\n"
            response += f"   ✅ GST Status: {company['gst_status'] or 'Unknown'}\n"
            response += f"   🏛️ Constitution: {company['constitution'] or 'N/A'}\n\n"
        
        return response
    
    def _format_product_response(self, results: Dict[str, Any]) -> str:
        """Format product search results"""
        if not results.get("results"):
            return "📦 No products found in the database."
        
        response = f"📦 **Product Search Results ({results['count']} found):**\n\n"
        
        for product in results["results"][:5]:
            response += f"📦 **{product['name']}**\n"
            response += f"   🏷️ HSN Code: {product['hsn_code']}\n"
            response += f"   💸 Tax Rate: {product['tax_rate']}%\n"
            response += f"   📝 Description: {product['description'] or 'N/A'}\n\n"
        
        return response
    
    def _format_financial_analysis_response(self, results: Dict[str, Any]) -> str:
        """Format financial analysis results"""
        summary = results.get("summary", {})
        monthly_trends = results.get("monthly_trends", [])
        top_suppliers = results.get("top_suppliers", [])
        
        response = "📊 **Financial Analysis Report:**\n\n"
        
        # Summary
        response += "📈 **Overall Summary:**\n"
        response += f"   🧾 Total Invoices: {summary.get('total_invoices', 0):,}\n"
        response += f"   💰 Total Amount: ₹{summary.get('total_amount', 0):,.2f}\n"
        response += f"   🏷️ Total Tax: ₹{summary.get('total_tax', 0):,.2f}\n"
        response += f"   📊 Taxable Value: ₹{summary.get('total_taxable', 0):,.2f}\n\n"
        
        # Monthly trends
        if monthly_trends:
            response += "📅 **Recent Monthly Trends:**\n"
            for trend in monthly_trends[:6]:
                response += f"   {trend['month']}: {trend['invoice_count']} invoices, ₹{trend['total_amount']:,.2f}\n"
            response += "\n"
        
        # Top suppliers
        if top_suppliers:
            response += "🏢 **Top Suppliers by Value:**\n"
            for supplier in top_suppliers[:5]:
                response += f"   {supplier['name']}: ₹{supplier['total_amount']:,.2f} ({supplier['invoice_count']} invoices)\n"
        
        return response
    
    def _format_payment_response(self, results: Dict[str, Any]) -> str:
        """Format payment search results"""
        if not results.get("results"):
            return "💳 No payment records found in the database."
        
        response = f"💳 **Payment Search Results ({results['count']} found):**\n\n"
        
        for payment in results["results"][:5]:
            response += f"💳 **Payment #{payment['payment_id']}**\n"
            response += f"   📅 Date: {payment['date']}\n"
            response += f"   💰 Amount: ₹{payment['amount']:,.2f}\n"
            response += f"   📊 Status: {payment['status']}\n"
            response += f"   🧾 Invoice: {payment['invoice_number']}\n\n"
        
        return response
    
    def _format_general_response(self, results: Dict[str, Any]) -> str:
        """Format general information response"""
        stats = results.get("database_stats", {})
        
        response = "💾 **Database Overview:**\n\n"
        response += f"📄 Invoices: {stats.get('invoices', 0):,}\n"
        response += f"🏢 Companies: {stats.get('companies', 0):,}\n"
        response += f"📦 Products: {stats.get('products', 0):,}\n\n"
        response += "I can help you with:\n"
        response += "• Invoice search and analysis\n"
        response += "• Company and GST information\n"
        response += "• Product and HSN code lookup\n"
        response += "• Financial reporting and trends\n"
        response += "• Payment tracking\n"
        response += "• Data validation\n"
        
        return response
    
    def close(self):
        """Close database connections"""
        self.db.close()
        self.gst_service.close()
        logger.info("📝 Chatbot connections closed")

def main():
    """Interactive CLI interface for the Simple Powerful Financial Chatbot"""
    print("🚀 Simple but Powerful Financial Chatbot")
    print("=" * 50)
    print("🤖 Initializing financial analysis system...")
    
    try:
        # Initialize the chatbot
        chatbot = SimplePowerfulFinancialChatbot("/Users/admin/gst-extractor/invoice_management.db")
        
        session_id = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💬 Session ID: {session_id}")
        print("\n🎯 Ready! I can help with:")
        print("📊 Invoice analysis and search")
        print("🏢 Company research with GST validation")
        print("📦 Product analysis and HSN code lookup")
        print("💰 Financial reporting and statistics")
        print("💳 Payment tracking and status")
        print("🔍 Database queries and validation")
        print("\nType 'quit' or 'exit' to end the session.")
        print("-" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\n💭 Your question: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Goodbye! Chat session ended.")
                    break
                
                if not user_input:
                    print("⚠️ Please enter a question.")
                    continue
                
                # Process with chatbot
                print("\n🤖 Processing your query...")
                start_time = datetime.now()
                
                response = chatbot.chat(user_input, session_id)
                
                processing_time = (datetime.now() - start_time).total_seconds()
                
                print(f"\n🎯 Response (processed in {processing_time:.2f}s):")
                print("-" * 50)
                print(response)
                print("-" * 50)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("Please try a different question.")
        
        # Cleanup
        chatbot.close()
        
    except Exception as e:
        print(f"💥 Failed to initialize chatbot: {str(e)}")
        print("Please check your database connections.")

if __name__ == "__main__":
    main()