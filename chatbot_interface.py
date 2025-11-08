#!/usr/bin/env python3
"""
Financial Chatbot Interface

Simple command-line interface for testing the financial database chatbot.
Provides interactive chat with memory persistence and financial data accuracy.
"""

import sys
import os
from datetime import datetime
import json

# Add the current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from financial_chatbot import FinancialChatbot
    print("✅ Successfully imported FinancialChatbot")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Installing required packages...")
    os.system("pip install langchain langgraph langchain-openai langchain-community")
    print("Please run the script again after installation.")
    sys.exit(1)

class ChatInterface:
    """Interactive chat interface for the financial chatbot"""
    
    def __init__(self):
        """Initialize the chat interface"""
        print("🚀 Initializing Financial Database Chatbot...")
        print("=" * 60)
        
        try:
            # Use Google Gemini as the default model
            self.chatbot = FinancialChatbot(
                model_name="gemini-2.5-flash",  # Latest Gemini 2.5 Flash model
                db_path="invoice_management.db",
                memory_path="chat_memory.db"
            )
            
            self.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"✅ Chatbot initialized successfully!")
            print(f"📝 Session ID: {self.session_id}")
            
        except Exception as e:
            print(f"❌ Failed to initialize chatbot: {e}")
            print("Make sure you have:")
            print("1. Set GOOGLE_API_KEY environment variable in .env file")
            print("2. Or use a different model (gpt-4o-mini for OpenAI, llama2 for Ollama)")
            sys.exit(1)
    
    def print_welcome(self):
        """Print welcome message and instructions"""
        print("\n" + "="*60)
        print("🏦 FINANCIAL DATABASE CHATBOT")
        print("="*60)
        print("I can help you with:")
        print("📊 Invoice search and analysis")
        print("🏢 Company and GST validation")
        print("📦 Product and HSN code lookup")
        print("💰 Financial reporting and trends")
        print("✅ Data validation and compliance checks")
        print("💳 Payment tracking and status")
        print("\nExamples:")
        print("• 'Show me all invoices from last month'")
        print("• 'Find company details for GSTIN 24AAXFA5297L1ZN'")
        print("• 'What's the total tax amount for all invoices?'")
        print("• 'Validate GSTIN 20AAHCI0488C121'")
        print("• 'Show payment status for recent invoices'")
        print("\nType 'help' for more options or 'quit' to exit.")
        print("="*60)
    
    def print_help(self):
        """Print detailed help information"""
        print("\n📚 DETAILED HELP")
        print("="*50)
        print("\n🔍 SEARCH COMMANDS:")
        print("• invoices [filter] - Search invoices")
        print("• companies [name/gstin] - Find companies")
        print("• products [name/hsn] - Search products")
        print("• payments [status] - Check payments")
        
        print("\n📊 ANALYSIS COMMANDS:")
        print("• total amount - Calculate totals")
        print("• monthly trends - Show monthly analysis")
        print("• tax summary - Tax breakdown")
        print("• compliance report - Check compliance")
        
        print("\n✅ VALIDATION COMMANDS:")
        print("• validate gstin [number] - Validate GST number")
        print("• check invoice [id] - Validate invoice")
        print("• verify company [name] - Check company")
        
        print("\n🔧 SYSTEM COMMANDS:")
        print("• help - Show this help")
        print("• memory - Show conversation memory")
        print("• stats - Show database statistics")
        print("• quit/exit - Close chatbot")
        print("="*50)
    
    def show_memory(self):
        """Show conversation memory and insights"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.chatbot.memory_path)
            cursor = conn.cursor()
            
            # Get session info
            cursor.execute("""
            SELECT COUNT(*) as total_messages,
                   AVG(confidence_score) as avg_confidence
            FROM chat_messages 
            WHERE session_id = ?
            """, (self.session_id,))
            
            stats = cursor.fetchone()
            
            print(f"\n🧠 CONVERSATION MEMORY - Session: {self.session_id}")
            print("="*50)
            print(f"Total queries: {stats[0] if stats[0] else 0}")
            print(f"Average confidence: {stats[1]:.2f if stats[1] else 0.0}")
            
            # Get recent queries
            cursor.execute("""
            SELECT query_type, content, confidence_score, timestamp
            FROM chat_messages 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 5
            """, (self.session_id,))
            
            recent = cursor.fetchall()
            if recent:
                print("\n📝 Recent Queries:")
                for query in recent:
                    print(f"• {query[0]}: {query[1][:50]}... (confidence: {query[2]:.2f})")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Error accessing memory: {e}")
    
    def show_stats(self):
        """Show database statistics"""
        try:
            conn = self.chatbot.db.conn
            cursor = conn.cursor()
            
            print("\n📊 DATABASE STATISTICS")
            print("="*40)
            
            # Count records in each table
            tables = ["documents", "companies", "gst_companies", "products", "invoices", "invoice_item", "payment"]
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"📁 {table}: {count} records")
                except:
                    print(f"📁 {table}: Table not found")
            
            print("="*40)
            
        except Exception as e:
            print(f"❌ Error accessing database: {e}")
    
    def run(self):
        """Run the interactive chat interface"""
        self.print_welcome()
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle system commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Thank you for using Financial Database Chatbot!")
                    break
                
                elif user_input.lower() == 'help':
                    self.print_help()
                    continue
                
                elif user_input.lower() == 'memory':
                    self.show_memory()
                    continue
                
                elif user_input.lower() == 'stats':
                    self.show_stats()
                    continue
                
                elif user_input.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    self.print_welcome()
                    continue
                
                # Process with chatbot
                print("\n🤖 Assistant: ", end="", flush=True)
                
                try:
                    response = self.chatbot.chat(user_input, self.session_id)
                    print(response)
                    
                except Exception as e:
                    print(f"❌ Error processing your request: {str(e)}")
                    print("Please try rephrasing your question or type 'help' for guidance.")
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            
            except Exception as e:
                print(f"\n❌ Unexpected error: {str(e)}")
                print("Type 'help' for assistance or 'quit' to exit.")
        
        # Cleanup
        try:
            self.chatbot.close()
            print("� Database connections closed.")
        except:
            pass

def main():
    """Main function to start the chat interface"""
    try:
        interface = ChatInterface()
        interface.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())