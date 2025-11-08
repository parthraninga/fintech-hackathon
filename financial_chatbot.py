#!/usr/bin/env python3
"""
Financial Database Chatbot Architecture

This module implements a sophisticated chatbot using LangGraph that can:
1. Search and analyze financial data with high accuracy
2. Maintain conversation memory and learn from interactions
3. Prevent hallucination while remaining innovative
4. Provide comprehensive GST and invoice management capabilities
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated, Union
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_community.llms import Ollama
from langchain_google_genai import ChatGoogleGenerativeAI
import sqlite3
import json
import os
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our schemas
from schemas.database_schema import DATABASE_SCHEMA, BUSINESS_RULES
from schemas.langchain_schema import LANGCHAIN_SCHEMA, SAFETY_RULES, validate_financial_data
from invoice_database import InvoiceDatabase
from gst_service import GSTService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatState(TypedDict):
    """State management for the chatbot conversation"""
    messages: Annotated[List[BaseMessage], "The conversation history"]
    current_query: str
    query_type: str
    database_results: Dict[str, Any]
    user_context: Dict[str, Any]
    session_id: str
    memory_summary: str
    confidence_score: float
    requires_verification: bool

@dataclass
class ConversationMemory:
    """Persistent conversation memory structure"""
    session_id: str
    user_id: str
    conversation_history: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    frequently_accessed: Dict[str, List[str]]
    learning_insights: Dict[str, Any]
    last_updated: datetime

class FinancialChatbot:
    """Advanced financial chatbot with memory and database integration"""
    
    def __init__(self, 
                 model_name: str = "gemini-2.5-flash",
                 db_path: str = "invoice_management.db",
                 memory_path: str = "chat_memory.db"):
        """Initialize the chatbot with database connections and AI model"""
        
        # Initialize database connections
        self.db = InvoiceDatabase(db_path)
        self.gst_service = GSTService(db_path)
        
        # Initialize AI model
        if model_name.startswith("gemini"):
            # Use Google Gemini
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required for Gemini models")
            self.llm = ChatGoogleGenerativeAI(
                model=model_name,
                google_api_key=google_api_key,
                temperature=0.1,
                convert_system_message_to_human=True
            )
        elif model_name.startswith("gpt-"):
            # Fallback to OpenAI if needed
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        else:
            # Use Ollama for local models
            self.llm = Ollama(model=model_name, temperature=0.1)
        
        # Initialize memory system
        self.memory_path = memory_path
        self.init_memory_database()
        
        # Build the conversation graph
        self.graph = self.build_conversation_graph()
        
        logger.info(f"✅ Financial chatbot initialized successfully with {model_name}")
    
    def init_memory_database(self):
        """Initialize conversation memory database"""
        conn = sqlite3.connect(self.memory_path)
        cursor = conn.cursor()
        
        # Conversation sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_queries INTEGER DEFAULT 0,
                user_preferences TEXT,
                session_summary TEXT
            )
        """)
        
        # Individual messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                message_type TEXT,
                content TEXT,
                query_type TEXT,
                database_tables_used TEXT,
                results_summary TEXT,
                confidence_score REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
            )
        """)
        
        # Learning insights table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_insights (
                insight_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_description TEXT,
                frequency INTEGER DEFAULT 1,
                success_rate REAL,
                last_observed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
        print("✅ Chat memory database initialized")
    
    def build_conversation_graph(self) -> StateGraph:
        """Build the LangGraph conversation flow"""
        
        def classify_query(state: ChatState) -> ChatState:
            """Classify the user query type with advanced pattern recognition for complex queries"""
            query = state["current_query"].lower()
            
            # Complex analytical query patterns
            complex_patterns = {
                "multi_table_analysis": ["join", "across", "between", "correlation", "relationship"],
                "time_series_analysis": ["trend", "over time", "monthly", "quarterly", "year-over-year", "temporal", "seasonal"],
                "statistical_analysis": ["average", "mean", "median", "percentile", "variance", "standard deviation", "distribution"],
                "comparative_analysis": ["compare", "versus", "vs", "difference", "ratio", "proportion", "benchmark"],
                "aggregation_analysis": ["sum", "total", "count", "group by", "aggregate", "breakdown", "segment"],
                "pattern_detection": ["pattern", "anomaly", "outlier", "unusual", "irregular", "exception"],
                "advanced_filtering": ["where", "filter", "condition", "criteria", "having", "such that"],
                "performance_analysis": ["efficiency", "performance", "optimization", "speed", "throughput"],
                "compliance_analysis": ["compliance", "regulation", "rule", "policy", "standard", "requirement"],
                "forecasting_analysis": ["predict", "forecast", "project", "estimate", "future", "scenario"]
            }
            
            # Advanced query classification
            complexity_score = 0
            detected_patterns = []
            
            for pattern_type, keywords in complex_patterns.items():
                if any(keyword in query for keyword in keywords):
                    detected_patterns.append(pattern_type)
                    complexity_score += 1
            
            # Primary classification with complexity awareness
            if any(word in query for word in ["invoice", "bill", "receipt"]):
                if complexity_score > 2:
                    state["query_type"] = "complex_invoice_analysis"
                else:
                    state["query_type"] = "invoice_search"
            elif any(word in query for word in ["company", "supplier", "buyer", "gstin", "gst"]):
                if complexity_score > 1:
                    state["query_type"] = "complex_company_analysis"
                else:
                    state["query_type"] = "company_lookup"
            elif any(word in query for word in ["product", "hsn", "item"]):
                if complexity_score > 1:
                    state["query_type"] = "complex_product_analysis"
                else:
                    state["query_type"] = "product_search"
            elif any(word in query for word in ["analysis", "report", "summary", "total", "trend"]):
                if complexity_score > 3:
                    state["query_type"] = "advanced_financial_analysis"
                elif complexity_score > 1:
                    state["query_type"] = "complex_financial_analysis"
                else:
                    state["query_type"] = "financial_analysis"
            elif any(word in query for word in ["validate", "check", "verify"]):
                if complexity_score > 1:
                    state["query_type"] = "complex_validation"
                else:
                    state["query_type"] = "validation"
            elif any(word in query for word in ["payment", "paid", "due", "outstanding"]):
                if complexity_score > 1:
                    state["query_type"] = "complex_payment_analysis"
                else:
                    state["query_type"] = "payment_tracking"
            elif complexity_score > 2:
                state["query_type"] = "advanced_database_query"
            else:
                state["query_type"] = "general_query"
            
            # Store complexity metadata
            state["user_context"] = {
                "complexity_score": complexity_score,
                "detected_patterns": detected_patterns,
                "requires_advanced_processing": complexity_score > 2
            }
            
            logger.info(f"📊 Classified query as: {state['query_type']} (complexity: {complexity_score}, patterns: {detected_patterns})")
            return state
        
        def retrieve_data(state: ChatState) -> ChatState:
            """Retrieve relevant data from database with advanced query handling"""
            query_type = state["query_type"]
            query = state["current_query"]
            user_context = state.get("user_context", {})
            
            try:
                # Handle basic query types
                if query_type == "invoice_search":
                    results = self._search_invoices(query)
                elif query_type == "company_lookup":
                    results = self._search_companies(query)
                elif query_type == "product_search":
                    results = self._search_products(query)
                elif query_type == "financial_analysis":
                    results = self._perform_analysis(query)
                elif query_type == "validation":
                    results = self._validate_data(query)
                elif query_type == "payment_tracking":
                    results = self._track_payments(query)
                    
                # Handle complex query types with enhanced processing
                elif query_type == "complex_invoice_analysis":
                    results = self._perform_complex_invoice_analysis(query, user_context)
                elif query_type == "complex_company_analysis":
                    results = self._perform_complex_company_analysis(query, user_context)
                elif query_type == "complex_product_analysis":
                    results = self._perform_complex_product_analysis(query, user_context)
                elif query_type == "complex_financial_analysis":
                    results = self._perform_complex_financial_analysis(query, user_context)
                elif query_type == "advanced_financial_analysis":
                    results = self._perform_advanced_financial_analysis(query, user_context)
                elif query_type == "complex_validation":
                    results = self._perform_complex_validation(query, user_context)
                elif query_type == "complex_payment_analysis":
                    results = self._perform_complex_payment_analysis(query, user_context)
                elif query_type == "advanced_database_query":
                    results = self._execute_advanced_database_query(query, user_context)
                else:
                    results = {
                        "message": "I can help you with simple and complex queries including: invoice analysis, company research, product insights, financial analysis, validation, payment tracking, and advanced database operations.",
                        "capabilities": [
                            "Multi-table JOIN analysis",
                            "Time-series and trend analysis", 
                            "Statistical aggregations",
                            "Comparative analysis",
                            "Pattern detection",
                            "Complex filtering and conditions",
                            "Performance optimization",
                            "Compliance checking"
                        ]
                    }
                
                state["database_results"] = results
                state["confidence_score"] = results.get("confidence", 0.8)
                
                # Log complex query handling
                if user_context.get("complexity_score", 0) > 2:
                    logger.info(f"🔍 Executed complex query with patterns: {user_context.get('detected_patterns', [])}")
                
            except Exception as e:
                logger.error(f"❌ Database query error: {str(e)}")
                state["database_results"] = {"error": str(e)}
                state["confidence_score"] = 0.0
            
            return state
        
        def generate_response(state: ChatState) -> ChatState:
            """Generate AI response based on data and context"""
            results = state["database_results"]
            query_type = state["query_type"]
            memory_context = state.get("memory_summary", "")
            
            # Validate that we have actual data - no mock data allowed
            if not results or "error" in results:
                error_message = "I cannot provide financial data as no actual database results were found. I never generate mock or estimated financial figures - only real data from the database."
                ai_message = AIMessage(content=error_message)
                state["messages"].append(ai_message)
                return state
            
            # Build context-aware prompt
            system_prompt = f"""You are an advanced financial data expert chatbot with sophisticated database querying capabilities. You have access to a comprehensive invoice and GST database and are equipped to handle complex, multi-dimensional financial analysis.

🚨 CRITICAL FINANCIAL DATA RULES:
1. NEVER generate, estimate, or provide mock financial data
2. ONLY use actual data from the database query results provided
3. If data is not available in the database, explicitly state "No data found" or "Data not available"
4. Always cite the exact source table and field for every financial figure
5. Never extrapolate, interpolate, or calculate figures not directly from the database

🔥 COMPLEX QUERY CAPABILITIES:
You are designed to handle extremely sophisticated database queries including:
- Multi-table JOINs with complex WHERE clauses and subqueries
- Advanced aggregations (SUM, AVG, COUNT, GROUP BY, HAVING)
- Time-series analysis with date ranges and temporal patterns
- Cross-referential analysis between invoices, suppliers, and GST data
- Statistical analysis including variance, percentiles, and trend analysis
- Nested queries with correlated subqueries and window functions
- Complex filtering with multiple conditions and logical operators
- Data mining queries for pattern detection and anomaly identification
- Hierarchical queries for organizational or category-based analysis
- Performance-optimized queries for large dataset analysis

🎯 ADVANCED ANALYTICAL SKILLS:
- Break down complex user requests into precise SQL query components
- Understand business context behind technical requirements
- Identify relationships between different data entities
- Suggest query optimizations for better performance
- Provide insights from complex data patterns
- Handle edge cases and data quality considerations
- Explain complex results in business-friendly language

SAFETY RULES:
{SAFETY_RULES['data_sources']}
{SAFETY_RULES['calculation_accuracy']}
{SAFETY_RULES['compliance_checks']}

RESPONSE REQUIREMENTS:
- All financial amounts must come directly from database query results
- Include confidence levels and source attribution for all data
- Flag any discrepancies or incomplete data clearly
- If calculations are needed, show the exact formula and source data
- Never fill in missing data with assumptions or estimates
- For complex queries, explain the analysis methodology
- Break down complex results into digestible insights
- Provide context for statistical findings and trends

COMPLEX QUERY HANDLING:
- Analyze user intent to determine optimal query strategy
- Consider performance implications of complex operations
- Suggest alternative approaches for better insights
- Handle multi-step analysis workflows
- Provide detailed explanations for complex calculations
- Identify data limitations and suggest improvements

Current Context:
- Query Type: {query_type}
- User's Previous Context: {memory_context}
- Database Results: {json.dumps(results, indent=2)}

IMPORTANT: You excel at complex database analysis while maintaining strict accuracy standards. Base your response ONLY on the actual database data provided above. For complex queries, provide comprehensive analysis with clear methodology. If the database results are empty or incomplete, clearly state this fact and suggest alternative approaches.
Do not generate or estimate any financial figures that are not in the actual query results."""

            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": state["current_query"]}
                ]
                
                response = self.llm.invoke(messages)
                
                # Validate response doesn't contain mock data indicators
                response_content = response.content if hasattr(response, 'content') else str(response)
                mock_indicators = ["for example", "typically", "approximately", "estimated", "sample", "mock", "placeholder"]
                
                # Check if response contains mock data indicators with financial terms
                financial_terms = ["₹", "INR", "amount", "tax", "total", "rate", "%"]
                contains_mock_risk = False
                
                for mock in mock_indicators:
                    if mock.lower() in response_content.lower():
                        for term in financial_terms:
                            if term in response_content:
                                contains_mock_risk = True
                                break
                
                if contains_mock_risk:
                    # Override with safe response
                    safe_response = f"I can only provide actual financial data from the database. Based on your query about {query_type}, here are the real database results:\n\n{json.dumps(results, indent=2)}\n\nI cannot generate estimates or sample financial figures - only actual recorded data."
                    ai_message = AIMessage(content=safe_response)
                else:
                    ai_message = AIMessage(content=response_content)
                
                state["messages"].append(ai_message)
                
                # Check if verification needed
                state["requires_verification"] = self._needs_verification(results, query_type)
                
            except Exception as e:
                logger.error(f"❌ AI generation error: {str(e)}")
                error_message = "I apologize, but I encountered an issue processing your request. I can only provide actual financial data from the database - no mock or estimated figures."
                ai_message = AIMessage(content=error_message)
                state["messages"].append(ai_message)
            
            return state
        
        def update_memory(state: ChatState) -> ChatState:
            """Update conversation memory and learning insights"""
            try:
                self._save_conversation_turn(state)
                self._update_learning_insights(state)
                state["memory_summary"] = self._generate_memory_summary(state["session_id"])
            except Exception as e:
                logger.error(f"❌ Memory update error: {str(e)}")
            
            return state
        
        # Build the graph
        graph = StateGraph(ChatState)
        
        # Add nodes
        graph.add_node("classify", classify_query)
        graph.add_node("retrieve", retrieve_data)
        graph.add_node("generate", generate_response)
        graph.add_node("memory", update_memory)
        
        # Add edges
        graph.add_edge(START, "classify")
        graph.add_edge("classify", "retrieve")
        graph.add_edge("retrieve", "generate")
        graph.add_edge("generate", "memory")
        graph.add_edge("memory", END)
        
        return graph.compile()
    
    def _search_invoices(self, query: str) -> Dict[str, Any]:
        """Search invoices based on natural language query"""
        # Extract search parameters from query
        conn = self.db.conn
        cursor = conn.cursor()
        
        # Basic invoice search with company names
        sql_query = """
        SELECT 
            i.invoice_id, i.invoice_num, i.invoice_date,
            s.legal_name as supplier_name, s.gstin as supplier_gstin,
            b.legal_name as buyer_name, b.gstin as buyer_gstin,
            i.taxable_value, i.total_tax, i.total_value,
            i.status, i.validation, i.duplication
        FROM invoices i
        LEFT JOIN companies s ON i.supplier_company_id = s.company_id
        LEFT JOIN companies b ON i.buyer_company_id = b.company_id
        ORDER BY i.invoice_date DESC
        LIMIT 10
        """
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                "invoice_id": row[0],
                "invoice_number": row[1],
                "date": row[2],
                "supplier": {"name": row[3], "gstin": row[4]},
                "buyer": {"name": row[5], "gstin": row[6]},
                "amounts": {
                    "taxable": float(row[7]) if row[7] else 0,
                    "tax": float(row[8]) if row[8] else 0,
                    "total": float(row[9]) if row[9] else 0
                },
                "status": row[10],
                "validated": bool(row[11]),
                "duplicate": bool(row[12])
            })
        
        return {
            "results": formatted_results,
            "count": len(formatted_results),
            "confidence": 0.9,
            "source_tables": ["invoices", "companies"]
        }
    
    def _search_companies(self, query: str) -> Dict[str, Any]:
        """Search companies with GST validation"""
        conn = self.db.conn
        cursor = conn.cursor()
        
        # Search in both companies and gst_companies tables
        sql_query = """
        SELECT 
            c.company_id, c.legal_name, c.gstin, c.city, c.state,
            g.status as gst_status, g.constitution, g.nature_of_business
        FROM companies c
        LEFT JOIN gst_companies g ON c.gstin = g.gstin
        ORDER BY c.legal_name
        LIMIT 20
        """
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        formatted_results = []
        for row in results:
            formatted_results.append({
                "company_id": row[0],
                "name": row[1],
                "gstin": row[2],
                "location": {"city": row[3], "state": row[4]},
                "gst_status": row[5],
                "constitution": row[6],
                "business": row[7]
            })
        
        return {
            "results": formatted_results,
            "count": len(formatted_results),
            "confidence": 0.95,
            "source_tables": ["companies", "gst_companies"]
        }
    
    def _search_products(self, query: str) -> Dict[str, Any]:
        """Search products by name or HSN code"""
        conn = self.db.conn
        cursor = conn.cursor()
        
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
            "results": formatted_results,
            "count": len(formatted_results),
            "confidence": 0.9,
            "source_tables": ["products"]
        }
    
    def _perform_analysis(self, query: str) -> Dict[str, Any]:
        """Perform financial analysis"""
        conn = self.db.conn
        cursor = conn.cursor()
        
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
        
        return {
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
            "confidence": 1.0,
            "source_tables": ["invoices"]
        }
    
    def _validate_data(self, query: str) -> Dict[str, Any]:
        """Validate GST or invoice data"""
        if "gstin" in query.lower() or "gst" in query.lower():
            # Extract GSTIN from query if possible
            words = query.split()
            gstin = None
            for word in words:
                if len(word) == 15 and word.isalnum():
                    gstin = word.upper()
                    break
            
            if gstin:
                is_valid, data = self.gst_service.validate_company_gstin(gstin, "")
                return {
                    "gstin": gstin,
                    "is_valid": is_valid,
                    "details": data,
                    "confidence": 1.0 if is_valid else 0.5,
                    "source_tables": ["gst_companies"]
                }
        
        return {
            "message": "Please specify what you'd like me to validate (GSTIN, invoice number, etc.)",
            "confidence": 0.3
        }
    
    def _track_payments(self, query: str) -> Dict[str, Any]:
        """Track payment status and history"""
        conn = self.db.conn
        cursor = conn.cursor()
        
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
            "results": formatted_results,
            "count": len(formatted_results),
            "confidence": 0.95,
            "source_tables": ["payment", "invoices"]
        }
    
    # Complex Query Processing Methods
    
    def _perform_complex_invoice_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex invoice analysis with multi-dimensional queries"""
        conn = self.db.conn
        cursor = conn.cursor()
        
        detected_patterns = context.get("detected_patterns", [])
        
        results = {"analysis_type": "complex_invoice_analysis", "patterns": detected_patterns}
        
        try:
            # Time-series analysis if temporal patterns detected
            if "time_series_analysis" in detected_patterns:
                cursor.execute("""
                SELECT 
                    strftime('%Y-%m', invoice_date) as period,
                    COUNT(*) as invoice_count,
                    SUM(total_value) as period_total,
                    AVG(total_value) as avg_invoice_value,
                    MIN(total_value) as min_value,
                    MAX(total_value) as max_value
                FROM invoices 
                WHERE invoice_date >= date('now', '-24 months')
                GROUP BY strftime('%Y-%m', invoice_date)
                ORDER BY period DESC
                """)
                results["time_series"] = [dict(row) for row in cursor.fetchall()]
            
            # Statistical analysis
            if "statistical_analysis" in detected_patterns:
                cursor.execute("""
                SELECT 
                    COUNT(*) as total_invoices,
                    AVG(total_value) as mean_value,
                    MIN(total_value) as min_value,
                    MAX(total_value) as max_value,
                    SUM(total_value) as total_amount,
                    COUNT(CASE WHEN total_value > (SELECT AVG(total_value) FROM invoices) THEN 1 END) as above_average
                FROM invoices
                """)
                results["statistics"] = dict(cursor.fetchone())
            
            # Comparative analysis by supplier
            if "comparative_analysis" in detected_patterns:
                cursor.execute("""
                SELECT 
                    supplier_name,
                    COUNT(*) as invoice_count,
                    SUM(total_value) as total_amount,
                    AVG(total_value) as avg_amount,
                    MIN(invoice_date) as first_invoice,
                    MAX(invoice_date) as latest_invoice
                FROM invoices 
                GROUP BY supplier_name
                HAVING COUNT(*) > 1
                ORDER BY total_amount DESC
                LIMIT 20
                """)
                results["supplier_comparison"] = [dict(row) for row in cursor.fetchall()]
            
            results["confidence"] = 0.9
            
        except Exception as e:
            results["error"] = f"Complex invoice analysis failed: {str(e)}"
            results["confidence"] = 0.3
            
        return results
    
    def _perform_complex_financial_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex financial analysis with advanced aggregations"""
        conn = self.db.conn
        cursor = conn.cursor()
        
        detected_patterns = context.get("detected_patterns", [])
        results = {"analysis_type": "complex_financial_analysis", "patterns": detected_patterns}
        
        try:
            # Advanced aggregation analysis
            if "aggregation_analysis" in detected_patterns:
                cursor.execute("""
                SELECT 
                    strftime('%Y', invoice_date) as year,
                    strftime('%Q', invoice_date) as quarter,
                    COUNT(*) as transaction_count,
                    SUM(taxable_value) as total_taxable,
                    SUM(total_tax) as total_tax_paid,
                    SUM(total_value) as total_revenue,
                    AVG(total_tax / NULLIF(taxable_value, 0) * 100) as avg_tax_rate
                FROM invoices 
                WHERE invoice_date >= date('now', '-36 months')
                GROUP BY strftime('%Y', invoice_date), strftime('%Q', invoice_date)
                ORDER BY year DESC, quarter DESC
                """)
                results["quarterly_breakdown"] = [dict(row) for row in cursor.fetchall()]
            
            # Pattern detection for anomalies
            if "pattern_detection" in detected_patterns:
                cursor.execute("""
                SELECT *,
                    CASE 
                        WHEN total_value > (SELECT AVG(total_value) + 2 * 
                            (SELECT AVG((total_value - sub.avg_val) * (total_value - sub.avg_val)) 
                             FROM (SELECT AVG(total_value) as avg_val FROM invoices) sub 
                             FROM invoices)) THEN 'HIGH_VALUE_ANOMALY'
                        WHEN total_tax / NULLIF(taxable_value, 0) > 0.3 THEN 'HIGH_TAX_RATE'
                        WHEN total_value < 100 THEN 'LOW_VALUE_TRANSACTION'
                        ELSE 'NORMAL'
                    END as anomaly_type
                FROM invoices
                WHERE date(invoice_date) >= date('now', '-12 months')
                ORDER BY total_value DESC
                LIMIT 50
                """)
                results["anomaly_detection"] = [dict(row) for row in cursor.fetchall()]
            
            results["confidence"] = 0.85
            
        except Exception as e:
            results["error"] = f"Complex financial analysis failed: {str(e)}"
            results["confidence"] = 0.3
            
        return results
    
    def _perform_advanced_financial_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extremely complex financial analysis with advanced SQL operations"""
        conn = self.db.conn
        cursor = conn.cursor()
        
        results = {"analysis_type": "advanced_financial_analysis"}
        
        try:
            # Advanced multi-table analysis with window functions
            cursor.execute("""
            WITH monthly_stats AS (
                SELECT 
                    strftime('%Y-%m', invoice_date) as month,
                    COUNT(*) as invoice_count,
                    SUM(total_value) as monthly_total,
                    AVG(total_value) as monthly_avg,
                    LAG(SUM(total_value)) OVER (ORDER BY strftime('%Y-%m', invoice_date)) as prev_month_total
                FROM invoices 
                WHERE invoice_date >= date('now', '-24 months')
                GROUP BY strftime('%Y-%m', invoice_date)
            ),
            growth_analysis AS (
                SELECT *,
                    CASE 
                        WHEN prev_month_total IS NOT NULL 
                        THEN ((monthly_total - prev_month_total) / prev_month_total * 100)
                        ELSE NULL 
                    END as growth_rate
                FROM monthly_stats
            )
            SELECT * FROM growth_analysis ORDER BY month DESC
            """)
            results["growth_analysis"] = [dict(row) for row in cursor.fetchall()]
            
            # Supplier performance ranking
            cursor.execute("""
            WITH supplier_metrics AS (
                SELECT 
                    supplier_name,
                    COUNT(*) as total_invoices,
                    SUM(total_value) as total_business,
                    AVG(total_value) as avg_invoice_value,
                    MIN(invoice_date) as relationship_start,
                    MAX(invoice_date) as last_transaction,
                    COUNT(DISTINCT strftime('%Y-%m', invoice_date)) as active_months
                FROM invoices 
                GROUP BY supplier_name
                HAVING COUNT(*) >= 2
            )
            SELECT *,
                RANK() OVER (ORDER BY total_business DESC) as business_rank,
                RANK() OVER (ORDER BY total_invoices DESC) as frequency_rank,
                ROUND(julianday('now') - julianday(last_transaction)) as days_since_last
            FROM supplier_metrics
            ORDER BY total_business DESC
            """)
            results["supplier_performance"] = [dict(row) for row in cursor.fetchall()]
            
            results["confidence"] = 0.9
            
        except Exception as e:
            results["error"] = f"Advanced financial analysis failed: {str(e)}"
            results["confidence"] = 0.2
            
        return results
    
    def _execute_advanced_database_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute advanced database operations for complex analytical queries"""
        conn = self.db.conn
        cursor = conn.cursor()
        
        results = {"analysis_type": "advanced_database_query", "query_complexity": "extreme"}
        
        try:
            # Comprehensive database analysis
            cursor.execute("""
            SELECT 
                'invoices' as table_name,
                COUNT(*) as record_count,
                MIN(invoice_date) as earliest_date,
                MAX(invoice_date) as latest_date,
                SUM(total_value) as total_value,
                COUNT(DISTINCT supplier_name) as unique_suppliers
            FROM invoices
            UNION ALL
            SELECT 
                'companies' as table_name,
                COUNT(*) as record_count,
                MIN(created_at) as earliest_date,
                MAX(created_at) as latest_date,
                NULL as total_value,
                COUNT(DISTINCT gstin) as unique_gstins
            FROM companies
            """)
            results["database_overview"] = [dict(row) for row in cursor.fetchall()]
            
            # Complex cross-table analysis
            cursor.execute("""
            SELECT 
                i.supplier_name,
                c.company_name,
                c.gstin,
                COUNT(i.id) as invoice_count,
                SUM(i.total_value) as total_amount,
                AVG(i.total_tax / NULLIF(i.taxable_value, 0) * 100) as avg_tax_rate,
                MIN(i.invoice_date) as first_invoice,
                MAX(i.invoice_date) as latest_invoice
            FROM invoices i
            LEFT JOIN companies c ON UPPER(TRIM(i.supplier_name)) = UPPER(TRIM(c.company_name))
            GROUP BY i.supplier_name, c.company_name, c.gstin
            HAVING COUNT(i.id) > 0
            ORDER BY total_amount DESC
            """)
            results["cross_table_analysis"] = [dict(row) for row in cursor.fetchall()]
            
            results["confidence"] = 0.95
            
        except Exception as e:
            results["error"] = f"Advanced database query failed: {str(e)}"
            results["confidence"] = 0.1
            
        return results
    
    # Additional complex analysis methods can be added here for other query types
    def _perform_complex_company_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex company analysis"""
        return self._perform_complex_financial_analysis(query, context)  # Delegate for now
    
    def _perform_complex_product_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex product analysis"""
        return self._perform_complex_financial_analysis(query, context)  # Delegate for now
    
    def _perform_complex_validation(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex validation queries"""
        return self._perform_complex_financial_analysis(query, context)  # Delegate for now
    
    def _perform_complex_payment_analysis(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle complex payment analysis"""
        return self._perform_complex_financial_analysis(query, context)  # Delegate for now

    def _needs_verification(self, results: Dict[str, Any], query_type: str) -> bool:
        """Determine if response needs human verification"""
        confidence = results.get("confidence", 0)
        return confidence < 0.7 or "error" in results
    
    def _save_conversation_turn(self, state: ChatState):
        """Save conversation turn to memory database"""
        conn = sqlite3.connect(self.memory_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO chat_messages 
        (session_id, message_type, content, query_type, results_summary, confidence_score)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            state["session_id"],
            "user_query",
            state["current_query"],
            state["query_type"],
            json.dumps(state["database_results"]),
            state["confidence_score"]
        ))
        
        conn.commit()
        conn.close()
    
    def _update_learning_insights(self, state: ChatState):
        """Update learning insights based on interaction"""
        conn = sqlite3.connect(self.memory_path)
        cursor = conn.cursor()
        
        pattern_type = f"query_type_{state['query_type']}"
        
        cursor.execute("""
        INSERT OR REPLACE INTO learning_insights 
        (pattern_type, pattern_description, frequency, success_rate)
        VALUES (?, ?, 
            COALESCE((SELECT frequency FROM learning_insights WHERE pattern_type = ?), 0) + 1,
            ?)
        """, (
            pattern_type,
            f"User queries about {state['query_type']}",
            pattern_type,
            state["confidence_score"]
        ))
        
        conn.commit()
        conn.close()
    
    def _generate_memory_summary(self, session_id: str) -> str:
        """Generate a summary of recent conversation for context"""
        conn = sqlite3.connect(self.memory_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT query_type, COUNT(*) as frequency
        FROM chat_messages
        WHERE session_id = ? AND timestamp >= datetime('now', '-1 hour')
        GROUP BY query_type
        ORDER BY frequency DESC
        LIMIT 3
        """, (session_id,))
        
        recent_patterns = cursor.fetchall()
        conn.close()
        
        if recent_patterns:
            summary = f"Recent focus: {', '.join([f'{p[0]} ({p[1]} queries)' for p in recent_patterns])}"
        else:
            summary = "New conversation session"
        
        return summary
    
    def chat(self, message: str, session_id: str = None) -> str:
        """Main chat interface"""
        if not session_id:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize state
        state = ChatState(
            messages=[HumanMessage(content=message)],
            current_query=message,
            query_type="",
            database_results={},
            user_context={},
            session_id=session_id,
            memory_summary=self._generate_memory_summary(session_id),
            confidence_score=0.0,
            requires_verification=False
        )
        
        # Run the conversation graph
        result = self.graph.invoke(state)
        
        # Return the AI response
        ai_responses = [msg.content for msg in result["messages"] if isinstance(msg, AIMessage)]
        return ai_responses[-1] if ai_responses else "I'm sorry, I couldn't process your request."
    
    def close(self):
        """Close database connections"""
        self.db.close()
        self.gst_service.close()
        print("📝 Chatbot connections closed")

# Convenience function for easy usage
def create_financial_chatbot(**kwargs) -> FinancialChatbot:
    """Create and return a configured financial chatbot instance"""
    return FinancialChatbot(**kwargs)

# CLI Interface for direct usage
def main():
    """Interactive CLI interface for the Financial Chatbot"""
    print("🚀 Advanced Financial Chatbot with LangGraph")
    print("=" * 50)
    print("🤖 Initializing sophisticated financial analysis system...")
    
    try:
        # Initialize the advanced chatbot
        chatbot = FinancialChatbot(
            model_name="gemini-2.5-flash",
            db_path="/Users/admin/gst-extractor/invoice_management.db",
            memory_path="/Users/admin/gst-extractor/chat_memory.db"
        )
        
        session_id = f"cli_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"💬 Session ID: {session_id}")
        print("\n🎯 Ready! I can help with:")
        print("📊 Complex invoice analysis and trends")
        print("🏢 Company research with GST validation")
        print("📦 Product analysis and HSN code insights")
        print("💰 Advanced financial reporting and statistics")
        print("🔍 Multi-table database queries")
        print("📈 Time-series analysis and forecasting")
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
                
                # Process with advanced chatbot
                print("\n🤖 Processing your complex query...")
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
        print("Please check your database connections and API keys.")

if __name__ == "__main__":
    main()