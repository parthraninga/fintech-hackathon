"""
GST Taxpayer Details Extractor using GSTZen with Playwright

This module extracts comprehensive taxpayer details from GSTZen by automating
the search form interaction using Playwright browser automation.

Quick Usage:
    from gst_extractor import extract_gst_details
    
    details = extract_gst_details("24AAXFA5297L1ZN")
    if details:
        print(f"Company: {details.legal_name}")
        print(f"Status: {details.status}")

Interactive Usage:
    python3 gst_extractor.py

Features:
- Extract by GSTIN number using automated browser interaction
- Complete taxpayer information extraction
- GST returns filing history
- Jurisdiction and registration details  
- JSON export with timestamps
- Handles dynamic form submissions and redirects
"""

import json
import time
import re
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Additional imports are already configured above

@dataclass
class TaxpayerDetails:
    """Data class to store taxpayer details"""
    gstin: str
    legal_name: str = ""
    trade_name: str = ""
    registration_date: str = ""
    constitution: str = ""
    taxpayer_type: str = ""
    status: str = ""
    pan: str = ""
    address: str = ""
    state: str = ""
    pin_code: str = ""
    nature_of_business: str = ""
    state_jurisdiction: str = ""
    centre_jurisdiction: str = ""
    cancellation_date: str = ""
    recent_returns: List[Dict[str, str]] = None
    api_source: str = "GSTZen"
    
    def __post_init__(self):
        if self.recent_returns is None:
            self.recent_returns = []

class GSTZenExtractor:
    """GST Taxpayer Details Extractor using Playwright browser automation"""
    
    def __init__(self):
        self.base_url = "https://my.gstzen.in"
        self.search_url = "https://my.gstzen.in/m/taxpayers/search/"
        
    def validate_gstin(self, gstin: str) -> bool:
        """
        Validate GST UIN format
        """
        if not gstin or len(gstin) != 15:
            return False
            
        pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z][Z][0-9A-Z]$'
        return bool(re.match(pattern, gstin.upper()))
    
    def extract_from_gstin(self, gstin: str) -> Optional[TaxpayerDetails]:
        """
        Extract taxpayer details by GSTIN using Playwright browser automation
        """
        if not self.validate_gstin(gstin):
            logger.error(f"Invalid GST UIN format: {gstin}")
            return None
            
        logger.info(f"Starting browser automation for GSTIN: {gstin}")
        
        with sync_playwright() as p:
            # Launch browser (use headless=False for debugging)
            browser = p.chromium.launch(headless=True)
            
            try:
                page = browser.new_page()
                
                # Set user agent to look more like a real browser
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                })
                
                # Navigate to search page
                logger.info(f"Navigating to: {self.search_url}")
                page.goto(self.search_url, wait_until="networkidle")
                
                # Wait for page to load
                page.wait_for_timeout(2000)
                
                # Fill in GSTIN field
                logger.info(f"Filling GSTIN field with: {gstin}")
                gstin_input = page.locator('input[name="gstin"]')
                gstin_input.fill(gstin.upper())
                
                # Clear other fields to make sure only GSTIN search is used
                pan_input = page.locator('input[name="pan"]')
                if pan_input.count() > 0:
                    pan_input.fill("")
                
                taxpayer_name_input = page.locator('input[name="name"]')
                if taxpayer_name_input.count() > 0:
                    taxpayer_name_input.fill("")
                
                # Find and click the search button
                logger.info("Clicking search button...")
                search_button = page.locator('button[type="submit"]:has-text("Search Tax Payer")')
                if search_button.count() == 0:
                    # Try alternative search button selectors
                    search_button = page.locator('input[type="submit"]')
                    if search_button.count() == 0:
                        search_button = page.locator('button[type="submit"]')
                
                if search_button.count() > 0:
                    search_button.click()
                    
                    # Wait for navigation/response
                    logger.info("Waiting for search results...")
                    page.wait_for_timeout(5000)
                    
                    # Check current URL
                    current_url = page.url
                    logger.info(f"Current URL after search: {current_url}")
                    
                    # Get page content
                    page_content = page.content()
                    
                    # Check if we're on a taxpayer details page
                    if '/m/taxpayers/' in current_url and current_url != self.search_url:
                        logger.info("Successfully redirected to taxpayer details page")
                        return self._parse_taxpayer_page(page_content, current_url)
                    else:
                        # Check if there are search results with links
                        return self._handle_search_results(page, gstin)
                else:
                    logger.error("Could not find search button")
                    return None
                    
            except Exception as e:
                logger.error(f"Browser automation error: {str(e)}")
                return None
            finally:
                browser.close()
    
    def _handle_search_results(self, page: Page, gstin: str) -> Optional[TaxpayerDetails]:
        """Handle search results page and look for taxpayer links"""
        try:
            logger.info("Handling search results page")
            
            # Look for links to taxpayer pages containing our GSTIN
            taxpayer_links = page.locator(f'a[href*="/m/taxpayers/"][href*="{gstin}"]')
            
            if taxpayer_links.count() > 0:
                # Click the first taxpayer link
                logger.info("Found taxpayer link in search results")
                taxpayer_links.first.click()
                
                # Wait for navigation
                page.wait_for_timeout(3000)
                
                # Get the new page content
                page_content = page.content()
                current_url = page.url
                
                logger.info(f"Navigated to taxpayer page: {current_url}")
                return self._parse_taxpayer_page(page_content, current_url)
            else:
                # Try looking for any text containing the GSTIN
                page_text = page.content()
                if gstin in page_text:
                    logger.info("GSTIN found in search results, extracting available info")
                    return self._parse_search_results_content(page_text, gstin)
                else:
                    logger.warning("GSTIN not found in search results")
                    return None
                    
        except Exception as e:
            logger.error(f"Error handling search results: {str(e)}")
            return None
    
    def _parse_search_results_content(self, html_content: str, gstin: str) -> Optional[TaxpayerDetails]:
        """Parse basic info from search results page"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            details = TaxpayerDetails(gstin=gstin, api_source="GSTZen Search Results")
            
            # Try to extract any visible information about the company
            text = soup.get_text()
            lines = text.split('\n')
            
            # Look for company name near the GSTIN
            for i, line in enumerate(lines):
                if gstin in line:
                    # Check surrounding lines for company name
                    for j in range(max(0, i-5), min(len(lines), i+6)):
                        candidate = lines[j].strip()
                        if candidate and len(candidate) > 10 and not candidate.isdigit() and gstin not in candidate:
                            # This might be a company name
                            if any(word in candidate.upper() for word in ['LTD', 'LIMITED', 'PRIVATE', 'PVT', 'COMPANY', 'CORP']):
                                details.legal_name = candidate
                                break
                    break
            
            return details if details.legal_name else None
            
        except Exception as e:
            logger.error(f"Error parsing search results content: {str(e)}")
            return None
    
    def _parse_taxpayer_page(self, html_content: str, url: str) -> Optional[TaxpayerDetails]:
        """Parse taxpayer details from GSTZen page HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract GSTIN from URL or page
            gstin_match = re.search(r'([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z][Z][0-9A-Z])', url)
            if not gstin_match:
                logger.error("Could not extract GSTIN from URL")
                return None
            
            gstin = gstin_match.group(1)
            details = TaxpayerDetails(gstin=gstin)
            
            # Parse the GSTIN Details table
            self._parse_gstin_details_table(soup, details)
            
            # Parse tax returns information
            self._parse_tax_returns(soup, details)
            
            # Parse additional information from text content
            self._parse_description_text(soup, details)
            
            logger.info(f"Successfully parsed taxpayer details for {gstin}")
            return details
            
        except Exception as e:
            logger.error(f"Error parsing taxpayer page: {str(e)}")
            return None
    
    def _parse_gstin_details_table(self, soup: BeautifulSoup, details: TaxpayerDetails):
        """Parse the GSTIN Details table"""
        try:
            # Find all table rows and parse key-value pairs
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) == 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    
                    # Map table fields to our data structure
                    field_mapping = {
                        'Legal Name': 'legal_name',
                        'Company Status': 'status',
                        'Trade Name': 'trade_name',
                        'GSTIN': 'gstin',
                        'PAN': 'pan',
                        'State': 'state',
                        'PIN Code': 'pin_code',
                        'TaxPayer Type': 'taxpayer_type',
                        'Constitution of Business': 'constitution',
                        'Registration Date': 'registration_date',
                        'Cancellation Date': 'cancellation_date',
                        'State Jurisdiction': 'state_jurisdiction',
                        'Centre Jurisdiction': 'centre_jurisdiction',
                        'Nature of Business Activities': 'nature_of_business'
                    }
                    
                    if key in field_mapping:
                        field_name = field_mapping[key]
                        
                        # Special handling for certain fields
                        if key == 'Nature of Business Activities':
                            # Extract business activities (remove bullet points)
                            activities = re.findall(r'▪\s*([^▪]+)', value)
                            if activities:
                                value = ', '.join([activity.strip() for activity in activities])
                        elif key == 'State':
                            # Clean up state format (remove state code prefix)
                            state_match = re.search(r'\d+\s*-\s*(.+?)(?:\s*\([^)]+\))?$', value)
                            if state_match:
                                value = state_match.group(1).strip()
                        
                        setattr(details, field_name, value)
            
        except Exception as e:
            logger.error(f"Error parsing GSTIN details table: {str(e)}")
    
    def _parse_tax_returns(self, soup: BeautifulSoup, details: TaxpayerDetails):
        """Parse tax returns information"""
        try:
            # Find the tax returns table
            returns_data = []
            
            # Look for table rows with return information
            rows = soup.find_all('tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:  # At least return type, period, and date
                    # Check if this looks like a return entry
                    return_type = cells[0].get_text(strip=True)
                    
                    # Look for common GST return types
                    if any(return_pattern in return_type.upper() for return_pattern in 
                          ['GSTR-1', 'GSTR-3B', 'GSTR1', 'GSTR3B', 'GSTR-2', 'GSTR-4', 'GSTR-5', 'GSTR-6', 'GSTR-7', 'GSTR-8', 'GSTR-9']):
                        
                        period = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        filed_date = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                        status = cells[3].get_text(strip=True) if len(cells) > 3 else "Filed"
                        
                        # Extract additional details if available
                        amount = ""
                        liability = ""
                        
                        if len(cells) > 4:
                            # Check if additional columns contain amount/liability info
                            for i in range(4, len(cells)):
                                cell_text = cells[i].get_text(strip=True)
                                if cell_text and ('₹' in cell_text or any(char.isdigit() for char in cell_text)):
                                    if not amount:
                                        amount = cell_text
                                    else:
                                        liability = cell_text
                        
                        return_entry = {
                            'return_type': return_type,
                            'period': period,
                            'filed_date': filed_date,
                            'status': status
                        }
                        
                        # Add financial details if available
                        if amount:
                            return_entry['amount'] = amount
                        if liability:
                            return_entry['liability'] = liability
                        
                        returns_data.append(return_entry)
            
            # Also look for returns in text content if table parsing didn't find enough
            if len(returns_data) < 3:
                self._parse_returns_from_text(soup, returns_data)
            
            details.recent_returns = returns_data[:15]  # Keep up to 15 recent returns
            logger.info(f"Found {len(details.recent_returns)} GST return entries")
            
        except Exception as e:
            logger.error(f"Error parsing tax returns: {str(e)}")
    
    def _parse_returns_from_text(self, soup: BeautifulSoup, existing_returns: List[Dict[str, str]]):
        """Parse additional return information from text content"""
        try:
            text_content = soup.get_text()
            
            # Look for return filing patterns in text
            return_patterns = [
                r'(GSTR-?[0-9][AB]?)\s+for\s+the\s+Return\s+Period\s+of\s+([^.]+?)\s+was\s+filed\s+on\s+([^.]+)',
                r'(GSTR[0-9][AB]?)\s+.*?([A-Za-z]+ 20\d{2})\s+.*?filed.*?(\d{1,2}-[A-Za-z]+-20\d{2})',
                r'(GSTR-[0-9][AB]?)\s*-\s*([^-]+?)\s*-\s*Filed:\s*([^,\n]+)'
            ]
            
            for pattern in return_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                
                for match in matches:
                    if len(match) >= 3:
                        return_type = match[0].strip()
                        period = match[1].strip()
                        filed_date = match[2].strip()
                        
                        # Check if this return is not already in the list
                        duplicate = False
                        for existing in existing_returns:
                            if (existing.get('return_type') == return_type and 
                                existing.get('period') == period):
                                duplicate = True
                                break
                        
                        if not duplicate:
                            existing_returns.append({
                                'return_type': return_type,
                                'period': period,
                                'filed_date': filed_date,
                                'status': 'Filed'
                            })
                            
        except Exception as e:
            logger.error(f"Error parsing returns from text: {str(e)}")
    
    def _parse_description_text(self, soup: BeautifulSoup, details: TaxpayerDetails):
        """Parse additional information from description text"""
        try:
            # Get the main text content
            text_content = soup.get_text()
            
            # Extract additional information that might not be in tables
            if not details.legal_name:
                # Try to extract from page title or heading
                title_match = re.search(r'^([^(]+)\s*\([^)]+\)', text_content)
                if title_match:
                    details.legal_name = title_match.group(1).strip()
            
            # Extract last return filed information
            returns_text = re.search(r'recently filed the following GST Returns:(.+?)(?:\n|$)', text_content, re.DOTALL)
            if returns_text and not details.recent_returns:
                returns_info = returns_text.group(1)
                # Parse return information from text
                return_matches = re.findall(r'(GSTR\d+[AB]?)\s+for\s+the\s+Return\s+Period\s+of\s+([^▪]+?)was\s+filed\s+on\s+([^▪]+)', returns_info)
                
                for match in return_matches:
                    details.recent_returns.append({
                        'return_type': match[0].strip(),
                        'period': match[1].strip(),
                        'filed_date': match[2].strip(),
                        'status': 'Filed'
                    })
            
        except Exception as e:
            logger.error(f"Error parsing description text: {str(e)}")
    
    def format_details(self, details: TaxpayerDetails) -> str:
        """Format taxpayer details for display"""
        if not details:
            return "No details found"
        
        formatted = f"""
╔══════════════════════════════════════════════════════════════╗
║                    GST TAXPAYER DETAILS                     ║
║                   Source: {details.api_source:<30} ║
╠══════════════════════════════════════════════════════════════╣
║ GST UIN          : {details.gstin:<40} ║
║ Legal Name       : {details.legal_name[:40]:<40} ║
║ Trade Name       : {details.trade_name[:40]:<40} ║
║ PAN Number       : {details.pan:<40} ║
║ Registration Date: {details.registration_date:<40} ║
║ Constitution     : {details.constitution[:40]:<40} ║
║ Taxpayer Type    : {details.taxpayer_type:<40} ║
║ Status           : {details.status:<40} ║
║ State            : {details.state[:40]:<40} ║
║ PIN Code         : {details.pin_code:<40} ║
║ Cancellation Date: {details.cancellation_date or 'N/A':<40} ║
║ State Jurisdiction: {details.state_jurisdiction[:39]:<39} ║
║ Centre Jurisdiction: {details.centre_jurisdiction[:38]:<38} ║
║ Nature of Business: {details.nature_of_business[:39]:<39} ║
╚══════════════════════════════════════════════════════════════╝
"""
        
        if details.recent_returns:
            formatted += "\n\nRecent GST Returns Filed:\n"
            formatted += "─" * 80 + "\n"
            formatted += f"{'Return Type':<12} {'Period':<15} {'Filed Date':<15} {'Status':<10} {'Amount':<15}\n"
            formatted += "─" * 80 + "\n"
            
            for return_info in details.recent_returns[:8]:  # Show last 8 returns
                formatted += f"{return_info.get('return_type', ''):<12} "
                formatted += f"{return_info.get('period', ''):<15} "
                formatted += f"{return_info.get('filed_date', ''):<15} "
                formatted += f"{return_info.get('status', ''):<10} "
                formatted += f"{return_info.get('amount', 'N/A'):<15}\n"
            
            # Add summary if there are more returns
            if len(details.recent_returns) > 8:
                formatted += f"\n... and {len(details.recent_returns) - 8} more returns (see JSON file for complete list)\n"
                
            # Add filing summary
            summary = self._create_returns_summary(details.recent_returns)
            if summary.get('return_types'):
                formatted += f"\nFiling Summary:\n"
                formatted += "─" * 40 + "\n"
                for return_type, count in summary['return_types'].items():
                    formatted += f"{return_type}: {count} filings\n"
                    
                if summary.get('latest_filing'):
                    latest = summary['latest_filing']
                    formatted += f"Latest: {latest.get('return_type', '')} for {latest.get('period', '')} filed on {latest.get('date_str', '')}\n"
        
        return formatted.strip()
    
    def save_to_json(self, details: TaxpayerDetails, filename: str = None) -> str:
        """Save taxpayer details to JSON file with comprehensive GST returns data"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"gst_details_{details.gstin}_{timestamp}.json"
        
        # Create comprehensive details dictionary
        details_dict = {
            'gstin': details.gstin,
            'legal_name': details.legal_name,
            'trade_name': details.trade_name,
            'pan': details.pan,
            'registration_date': details.registration_date,
            'constitution': details.constitution,
            'taxpayer_type': details.taxpayer_type,
            'status': details.status,
            'state': details.state,
            'pin_code': details.pin_code,
            'cancellation_date': details.cancellation_date,
            'state_jurisdiction': details.state_jurisdiction,
            'centre_jurisdiction': details.centre_jurisdiction,
            'nature_of_business': details.nature_of_business,
            'api_source': details.api_source,
            'extracted_on': datetime.now().isoformat(),
            
            # Enhanced GST Returns Section
            'gst_returns': {
                'total_returns_filed': len(details.recent_returns),
                'returns_summary': self._create_returns_summary(details.recent_returns),
                'detailed_filings': details.recent_returns
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(details_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Details saved to {filename}")
        logger.info(f"GST Returns: {len(details.recent_returns)} entries saved")
        return filename
    
    def _create_returns_summary(self, returns_list: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create a summary of GST returns filed"""
        try:
            summary = {
                'total_filings': len(returns_list),
                'return_types': {},
                'filing_frequency': {},
                'latest_filing': None,
                'oldest_filing': None
            }
            
            if not returns_list:
                return summary
            
            # Count return types
            for return_entry in returns_list:
                return_type = return_entry.get('return_type', 'Unknown')
                summary['return_types'][return_type] = summary['return_types'].get(return_type, 0) + 1
            
            # Analyze filing frequency by year
            for return_entry in returns_list:
                filed_date = return_entry.get('filed_date', '')
                if filed_date:
                    # Extract year from date (handle various date formats)
                    year_match = re.search(r'20\d{2}', filed_date)
                    if year_match:
                        year = year_match.group(0)
                        summary['filing_frequency'][year] = summary['filing_frequency'].get(year, 0) + 1
            
            # Find latest and oldest filings
            dated_returns = []
            for return_entry in returns_list:
                filed_date = return_entry.get('filed_date', '')
                if filed_date:
                    dated_returns.append({
                        'date_str': filed_date,
                        'return_type': return_entry.get('return_type', ''),
                        'period': return_entry.get('period', '')
                    })
            
            if dated_returns:
                # Sort by date string (approximate sorting)
                try:
                    dated_returns.sort(key=lambda x: x['date_str'], reverse=True)
                    summary['latest_filing'] = dated_returns[0]
                    summary['oldest_filing'] = dated_returns[-1]
                except:
                    # If sorting fails, just take first and last
                    summary['latest_filing'] = dated_returns[0]
                    summary['oldest_filing'] = dated_returns[-1]
            
            return summary
            
        except Exception as e:
            logger.error(f"Error creating returns summary: {str(e)}")
            return {'total_filings': len(returns_list), 'error': str(e)}

def extract_by_gstin_interactive():
    """Interactive function to extract details by GSTIN"""
    print("GST Taxpayer Details Extractor - GSTZen")
    print("=" * 50)
    print("Enter GSTIN to extract complete taxpayer details")
    print()
    
    extractor = GSTZenExtractor()
    
    while True:
        gstin = input("Enter GSTIN (or 'quit' to exit): ").strip().upper()
        
        if gstin.lower() in ['quit', 'exit', 'q']:
            print("Goodbye! 👋")
            break
        
        if not gstin:
            print("❌ Please enter a valid GSTIN")
            continue
        
        if not extractor.validate_gstin(gstin):
            print("❌ Invalid GSTIN format!")
            print("   GSTIN should be 15 characters: 2-digit state + 10-digit PAN + 3 other characters")
            print("   Example: 24AAXFA5297L1ZN")
            continue
        
        print(f"\n🔍 Searching for GSTIN: {gstin}")
        print("-" * 50)
        
        try:
            # Try to extract using GSTIN search
            details = extractor.extract_from_gstin(gstin)
            
            if details:
                print("✅ Successfully extracted taxpayer details!")
                print()
                print(extractor.format_details(details))
                
                # Ask if user wants to save
                save_choice = input("\nSave to JSON file? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    filename = extractor.save_to_json(details)
                    print(f"📁 Saved to: {filename}")
                
                # Show complete summary
                print(f"\n📊 COMPLETE DETAILS SUMMARY:")
                print(f"   GSTIN: {details.gstin}")
                print(f"   Legal Name: {details.legal_name}")
                print(f"   Trade Name: {details.trade_name}")
                print(f"   PAN: {details.pan}")
                print(f"   Status: {details.status}")
                print(f"   Constitution: {details.constitution}")
                print(f"   State: {details.state}")
                print(f"   PIN Code: {details.pin_code}")
                print(f"   Registration Date: {details.registration_date}")
                print(f"   Business Activities: {details.nature_of_business}")
                print(f"   State Jurisdiction: {details.state_jurisdiction}")
                print(f"   Centre Jurisdiction: {details.centre_jurisdiction}")
                print(f"   Recent Returns: {len(details.recent_returns)} entries")
                
                if details.recent_returns:
                    print(f"\n📋 Recent GST Returns:")
                    for i, return_info in enumerate(details.recent_returns[:5], 1):
                        print(f"   {i}. {return_info.get('return_type', '')} - {return_info.get('period', '')} (Filed: {return_info.get('filed_date', '')})")
                
            else:
                print("❌ Failed to extract taxpayer details")
                print("   Possible reasons:")
                print("   - GSTIN not found in GSTZen database")
                print("   - Network connectivity issues")
                print("   - GSTZen website structure changed")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "="*50)

def main():
    """Main function with options"""
    print("GST Taxpayer Details Extractor - GSTZen")
    print("=" * 50)
    print()
    print("Choose an option:")
    print("1. Extract by GSTIN (Interactive)")
    print("2. Extract from specific URL")
    print("3. Test with sample GSTIN")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        extract_by_gstin_interactive()
    
    elif choice == "2":
        extractor = GSTZenExtractor()
        url = input("Enter GSTZen URL: ").strip()
        
        if url:
            print(f"\n🔍 Extracting from URL: {url}")
            details = extractor.extract_from_url(url)
            
            if details:
                print("✅ Success!")
                print(extractor.format_details(details))
                filename = extractor.save_to_json(details)
                print(f"\n📁 Saved to: {filename}")
            else:
                print("❌ Failed to extract details")
    
    elif choice == "3":
        extractor = GSTZenExtractor()
        test_gstin = "24AAXFA5297L1ZN"
        
        print(f"\n🔍 Testing with sample GSTIN: {test_gstin}")
        print("-" * 50)
        
        details = extractor.extract_from_gstin(test_gstin)
        
        if details:
            print("✅ Successfully extracted taxpayer details!")
            print(extractor.format_details(details))
            
            filename = extractor.save_to_json(details)
            print(f"\n📁 Details saved to: {filename}")
            
            print(f"\n📊 COMPLETE SUMMARY:")
            print(f"   Company: {details.legal_name}")
            print(f"   GSTIN: {details.gstin}")
            print(f"   Status: {details.status}")
            print(f"   State: {details.state}")
            print(f"   Business: {details.nature_of_business}")
            print(f"   Returns Filed: {len(details.recent_returns)} recent entries")
        else:
            print("❌ Failed to extract taxpayer details")
    
    else:
        print("❌ Invalid choice")

# Function for direct GSTIN extraction (can be imported)
def extract_gst_details(gstin: str) -> Optional[TaxpayerDetails]:
    """
    Direct function to extract GST details by GSTIN
    
    Args:
        gstin: GST identification number
        
    Returns:
        TaxpayerDetails object with all extracted information or None
    """
    extractor = GSTZenExtractor()
    return extractor.extract_from_gstin(gstin)

if __name__ == "__main__":
    main()

# Simple Usage Examples:
# 
# 1. Command Line:
#    python3 gst_extractor.py
#
# 2. Import and use:
#    from gst_extractor import extract_gst_details
#    details = extract_gst_details("24AAXFA5297L1ZN")
#
# 3. Get all details:
#    if details:
#        print(f"Company: {details.legal_name}")
#        print(f"Status: {details.status}")
#        print(f"Business: {details.nature_of_business}")
#        print(f"Returns: {len(details.recent_returns)} entries")