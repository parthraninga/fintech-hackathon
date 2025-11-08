#!/usr/bin/env python3
"""
GST Service Integration

Provides GST validation and company information retrieval with:
1. Database-first lookup (for caching)
2. API fallback when not found locally
3. Company name fuzzy matching
4. Automatic storage of new GST data
"""

import json
import os
import subprocess
import tempfile
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from invoice_database import InvoiceDatabase

class GSTService:
    """GST Service for company validation and information retrieval"""
    
    def __init__(self, db_path: str = "invoice_management.db", quick_mode: bool = False):
        """Initialize GST service with database connection"""
        self.db = InvoiceDatabase(db_path)
        self.gst_extractor_path = "gst_extractor.py"
        self.quick_mode = quick_mode  # Skip API calls in quick mode
        
    def validate_company_gstin(self, gstin: str, company_name: str = None) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate company GSTIN and return GST information
        
        Returns:
            Tuple[bool, Dict]: (is_valid, gst_data)
        """
        print(f"\n🔍 Searching for GSTIN: {gstin}")
        print("-" * 50)
        
        # Step 1: Check database first
        existing_gst = self.db.get_gst_company(gstin)
        if existing_gst:
            print(f"✅ Found in database: {existing_gst.get('legal_name', 'Unknown')}")
            print(f"   Status: {existing_gst.get('status', 'Unknown')}")
            print(f"   State: {existing_gst.get('state', 'Unknown')}")
            print(f"   Constitution: {existing_gst.get('constitution', 'Unknown')}")
            
            # Check company name matching if provided
            if company_name:
                match_score = self._check_company_name_match(company_name, existing_gst)
                existing_gst['name_match_score'] = match_score
                
                if match_score < 0.5:
                    print(f"⚠️  Company name mismatch: {match_score:.2f} similarity")
                    print(f"   Input: {company_name}")
                    print(f"   GST Legal Name: {existing_gst.get('legal_name', 'Unknown')}")
                    existing_gst['name_mismatch_warning'] = True
                else:
                    print(f"✅ Company name matches: {match_score:.2f} similarity")
            
            return True, existing_gst
        
        # Step 2: Call API if not found in database
        print(f"📡 Not found in database, calling GST API...")
        
        # First check if we have recent GST files locally
        existing_file = self._check_existing_gst_file(gstin)
        if existing_file:
            print(f"📁 Found existing GST file: {existing_file}")
            print(f"   Loading from local file instead of API...")
            try:
                with open(existing_file, 'r', encoding='utf-8') as f:
                    gst_data = json.load(f)
                print(f"✅ Successfully loaded from existing file")
            except Exception as e:
                print(f"❌ Error loading existing file: {e}")
                gst_data = None
        else:
            print("   No existing files found, launching GST extractor...")
            gst_data = self._fetch_gst_from_api(gstin)
        
        if not gst_data:
            print(f"❌ Failed to extract taxpayer details")
            print("   Possible reasons:")
            print("   - GSTIN not found in GSTZen database")
            print("   - Network connectivity issues")
            print("   - GST extractor execution failed")
            return False, {}
        
        # Step 3: Store in database for future use
        print(f"✅ Successfully extracted taxpayer details!")
        print(f"   Legal Name: {gst_data.get('legal_name', 'Unknown')}")
        print(f"   Status: {gst_data.get('status', 'Unknown')}")
        print(f"   State: {gst_data.get('state', 'Unknown')}")
        
        print(f"💾 Storing GST data in database...")
        self.db.store_gst_data(gst_data)
        print(f"📁 Saved to database for future lookups")
        
        # Step 4: Check company name matching
        if company_name:
            match_score = self._check_company_name_match(company_name, gst_data)
            gst_data['name_match_score'] = match_score
            
            if match_score < 0.5:
                print(f"⚠️  Company name mismatch: {match_score:.2f} similarity")
                print(f"   Input: {company_name}")
                print(f"   GST Legal Name: {gst_data.get('legal_name', 'Unknown')}")
                gst_data['name_mismatch_warning'] = True
            else:
                print(f"✅ Company name matches: {match_score:.2f} similarity")
        
        return True, gst_data
    
    def search_companies_by_name(self, company_name: str, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for companies by name with fuzzy matching"""
        print(f"\n🔍 Searching companies by name: {company_name}")
        print("-" * 50)
        
        matches = self.db.search_companies_by_name(company_name, threshold)
        
        if matches:
            print(f"✅ Found {len(matches)} potential matches")
            print(f"\n📊 SEARCH RESULTS:")
            for i, match in enumerate(matches[:5], 1):  # Show top 5
                print(f"   {i}. {match.get('legal_name', 'Unknown')}")
                print(f"      GSTIN: {match.get('gstin', 'N/A')}")
                print(f"      Similarity: {match.get('similarity_score', 0):.2f}")
                print(f"      Status: {match.get('status', 'Unknown')}")
                print()
        else:
            print(f"❌ No matches found above threshold {threshold}")
            print("   Try lowering the threshold or checking the company name spelling")
        
        return matches
    
    def _check_existing_gst_file(self, gstin: str) -> Optional[str]:
        """Check if we have existing GST files for this GSTIN"""
        json_dir = "json-gst_extractor"
        if not os.path.exists(json_dir):
            return None
        
        # Find GST files for this GSTIN
        gst_files = [f for f in os.listdir(json_dir) if f.startswith(f"gst_details_{gstin}") and f.endswith('.json')]
        
        if not gst_files:
            return None
        
        # Get the most recent file
        latest_file = max(gst_files, key=lambda f: os.path.getctime(os.path.join(json_dir, f)))
        return os.path.join(json_dir, latest_file)
    
    def _fetch_gst_from_api(self, gstin: str) -> Optional[dict]:
        """Fetch GST data from API using subprocess"""
        try:
            print("� Not found in database, calling GST API...")
            
            # Check if file already exists
            json_file = f"{gstin}.json"
            if os.path.exists(json_file):
                print(f"✅ Found existing file: {json_file}")
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    return data
            
            print("   No existing files found, launching GST extractor...")
            print("🚀 Starting GST extraction process...")
            
            # Create the command
            command = ["python3", "gst_extractor.py", gstin]
            print(f"   Command: {' '.join(command)}")
            
            # Start the process with real-time output
            print(f"⏳ Executing GST extractor...")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Monitor with timeout and real-time output
            start_time = time.time()
            timeout = 60  # 60 seconds timeout
            output_lines = []
            
            while True:
                # Check for timeout
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    print("❌ Process timeout after 60s, terminating...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    break
                
                # Try to read output
                try:
                    line = process.stdout.readline()
                    if line:
                        line = line.strip()
                        if line:  # Only print non-empty lines
                            print(f"   {line}")
                            output_lines.append(line)
                    
                    # Check if process finished
                    if process.poll() is not None:
                        # Read any remaining output
                        remaining = process.stdout.read()
                        if remaining:
                            for remaining_line in remaining.strip().split('\n'):
                                if remaining_line.strip():
                                    print(f"   {remaining_line.strip()}")
                                    output_lines.append(remaining_line.strip())
                        break
                        
                except Exception as read_error:
                    # If we can't read, just check if process is done
                    if process.poll() is not None:
                        break
                    time.sleep(0.1)
            
            # Get the result
            return_code = process.poll()
            if return_code == 0:
                print("✅ GST extractor completed successfully!")
                
                # Try to load the generated file
                if os.path.exists(json_file):
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        
                    # Store in database for future use
                    self._store_gst_data(data)
                    return data
                else:
                    print(f"❌ Expected file {json_file} was not created")
                    return None
            else:
                print("❌ Failed to extract taxpayer details")
                print("   Possible reasons:")
                print("   - GSTIN not found in GSTZen database")
                print("   - Network connectivity issues") 
                print("   - GST extractor execution failed")
                return None
                
        except Exception as e:
            print(f"❌ Error calling GST API: {str(e)}")
            return None
    
    def _check_company_name_match(self, input_name: str, gst_data: Dict[str, Any]) -> float:
        """Check how well the input company name matches GST data"""
        if not input_name:
            return 0.0
        
        legal_name = gst_data.get('legal_name', '')
        trade_name = gst_data.get('trade_name', '')
        
        # Calculate similarity with both legal and trade names
        legal_similarity = self.db._calculate_similarity(input_name.lower(), legal_name.lower())
        trade_similarity = self.db._calculate_similarity(input_name.lower(), trade_name.lower())
        
        # Return the higher similarity score
        return max(legal_similarity, trade_similarity)
    
    def get_company_recommendations(self, company_name: str, gstin: str = None) -> Dict[str, Any]:
        """Get recommendations for company data inconsistencies"""
        recommendations = {
            "action": "proceed",
            "warnings": [],
            "suggestions": [],
            "confidence": 1.0
        }
        
        # If GSTIN provided, validate it
        if gstin:
            is_valid, gst_data = self.validate_company_gstin(gstin, company_name)
            
            if not is_valid:
                recommendations["action"] = "reject"
                recommendations["warnings"].append(f"Invalid GSTIN: {gstin}")
                recommendations["confidence"] = 0.0
                return recommendations
            
            # Check name matching
            name_match_score = gst_data.get('name_match_score', 1.0)
            if name_match_score < 0.5:
                recommendations["action"] = "review"
                recommendations["warnings"].append(f"Company name mismatch (similarity: {name_match_score:.2f})")
                recommendations["suggestions"].append(f"Expected name: {gst_data.get('legal_name', 'Unknown')}")
                recommendations["confidence"] = name_match_score
            
            # Check GST status
            gst_status = gst_data.get('status', '').lower()
            if gst_status != 'active':
                recommendations["warnings"].append(f"GST status is not active: {gst_status}")
                recommendations["confidence"] *= 0.8
        
        # Search for similar companies by name
        similar_companies = self.search_companies_by_name(company_name, threshold=0.6)
        if similar_companies:
            for company in similar_companies[:2]:  # Top 2 matches
                recommendations["suggestions"].append(
                    f"Similar company found: {company.get('legal_name')} (GSTIN: {company.get('gstin')}) "
                    f"- {company.get('similarity_score', 0):.2f} similarity"
                )
        
        return recommendations
    
    def close(self):
        """Close database connection"""
        if self.db:
            self.db.close()

# Example usage and testing
def main():
    """Test the GST service"""
    print("🧪 GST Service Testing")
    print("=" * 50)
    
    gst_service = GSTService()
    
    # Test with the provided GSTIN
    test_gstin = "24AAXFA5297L1ZN"
    test_company = "ARIHANT TRADE WORLD"
    
    print(f"\n1. Testing GSTIN validation: {test_gstin}")
    is_valid, gst_data = gst_service.validate_company_gstin(test_gstin, test_company)
    
    if is_valid:
        print(f"\n📊 COMPLETE GST DETAILS SUMMARY:")
        print(f"   GSTIN: {gst_data.get('gstin', 'N/A')}")
        print(f"   Legal Name: {gst_data.get('legal_name', 'N/A')}")
        print(f"   Trade Name: {gst_data.get('trade_name', 'N/A')}")
        print(f"   PAN: {gst_data.get('pan', 'N/A')}")
        print(f"   Status: {gst_data.get('status', 'N/A')}")
        print(f"   Constitution: {gst_data.get('constitution', 'N/A')}")
        print(f"   State: {gst_data.get('state', 'N/A')}")
        print(f"   PIN Code: {gst_data.get('pin_code', 'N/A')}")
        print(f"   Registration Date: {gst_data.get('registration_date', 'N/A')}")
        if 'name_match_score' in gst_data:
            print(f"   Name Match Score: {gst_data['name_match_score']:.2f}")
    else:
        print(f"❌ Validation failed")
    
    print(f"\n2. Testing company name search")
    matches = gst_service.search_companies_by_name("ARIHANT")
    
    print(f"\n3. Testing recommendations")
    recommendations = gst_service.get_company_recommendations(test_company, test_gstin)
    print(f"\n📋 RECOMMENDATIONS:")
    print(f"   Action: {recommendations['action']}")
    print(f"   Confidence: {recommendations['confidence']:.2f}")
    if recommendations['warnings']:
        print(f"   Warnings:")
        for warning in recommendations['warnings']:
            print(f"      • {warning}")
    if recommendations['suggestions']:
        print(f"   Suggestions:")
        for suggestion in recommendations['suggestions']:
            print(f"      • {suggestion}")
    
    gst_service.close()

if __name__ == "__main__":
    main()