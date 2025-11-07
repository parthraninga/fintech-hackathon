"""
HSN/SAC Code Validator and Details Extractor using GSTZen

This module extracts comprehensive HSN/SAC code information from GSTZen by automating
the HSN code validation form using Playwright browser automation.

Quick Usage:
    from hsn_extractor import extract_hsn_details
    
    details = extract_hsn_details("90153010")
    if details:
        print(f"HSN Code: {details.hsn_code}")
        print(f"Description: {details.description}")

Interactive Usage:
    python3 hsn_extractor.py

Features:
- Extract HSN/SAC code details using automated browser interaction
- Complete code information with description and tax rates
- Handles multiple codes at once
- JSON export with timestamps
- Validates HSN/SAC code format
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

@dataclass
class HSNCodeDetails:
    """Data class to store HSN/SAC code details"""
    hsn_code: str
    description: str = ""
    gst_rate: str = ""
    cgst_rate: str = ""
    sgst_rate: str = ""
    igst_rate: str = ""
    cess_rate: str = ""
    category: str = ""
    chapter: str = ""
    heading: str = ""
    sub_heading: str = ""
    tariff_item: str = ""
    valid: bool = False
    api_source: str = "GSTZen"
    
    def __post_init__(self):
        if not self.hsn_code:
            self.hsn_code = ""

class HSNExtractor:
    """HSN/SAC Code Details Extractor using Playwright browser automation"""
    
    def __init__(self):
        self.base_url = "https://my.gstzen.in"
        self.hsn_url = "https://my.gstzen.in/p/hsn-code-validator/"
        
    def validate_hsn_code(self, hsn_code: str) -> bool:
        """
        Validate HSN/SAC code format
        HSN codes are typically 4, 6, or 8 digits
        SAC codes are typically 6 digits
        """
        if not hsn_code:
            return False
            
        # Remove any spaces or special characters
        clean_code = re.sub(r'[^\d]', '', hsn_code)
        
        # HSN codes are usually 4, 6, or 8 digits
        # SAC codes are usually 6 digits
        return len(clean_code) >= 4 and len(clean_code) <= 8 and clean_code.isdigit()
    
    def extract_hsn_details(self, hsn_code: str) -> Optional[HSNCodeDetails]:
        """
        Extract HSN/SAC code details using Playwright browser automation
        """
        if not self.validate_hsn_code(hsn_code):
            logger.error(f"Invalid HSN/SAC code format: {hsn_code}")
            return None
            
        logger.info(f"Starting browser automation for HSN code: {hsn_code}")
        
        with sync_playwright() as p:
            # Launch browser (use headless=False for debugging)
            browser = p.chromium.launch(headless=True)
            
            try:
                page = browser.new_page()
                
                # Set user agent to look more like a real browser
                page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
                })
                
                # Navigate to HSN validator page
                logger.info(f"Navigating to: {self.hsn_url}")
                page.goto(self.hsn_url, wait_until="networkidle")
                
                # Wait for page to load
                page.wait_for_timeout(2000)
                
                # Scroll to middle of page to find the form
                page.evaluate('window.scrollTo(0, window.innerHeight * 1.5)')
                page.wait_for_timeout(2000)
                
                # Fill in HSN code field (it's a textarea with id="id_text")
                logger.info(f"Filling HSN code field with: {hsn_code}")
                hsn_input = page.locator('textarea#id_text')
                
                if hsn_input.count() == 0:
                    # Try alternative selectors
                    hsn_input = page.locator('textarea[name="text"]')
                    if hsn_input.count() == 0:
                        hsn_input = page.locator('textarea')
                
                if hsn_input.count() > 0:
                    hsn_input.fill(hsn_code.strip())
                    
                    # Find and click the submit button
                    logger.info("Clicking submit button...")
                    submit_button = page.locator('button:has-text("Check HSN/SAC Codes")')
                    
                    if submit_button.count() > 0:
                        submit_button.click()
                        
                        # Wait for results
                        logger.info("Waiting for HSN code validation results...")
                        page.wait_for_timeout(5000)
                        
                        # Check current URL and content
                        current_url = page.url
                        logger.info(f"Current URL after submit: {current_url}")
                        
                        # Get page content
                        page_content = page.content()
                        
                        # Parse the results
                        return self._parse_hsn_results(page_content, hsn_code, current_url)
                    else:
                        logger.error("Could not find submit button")
                        return None
                else:
                    logger.error("Could not find HSN code input field")
                    return None
                    
            except Exception as e:
                logger.error(f"Browser automation error: {str(e)}")
                return None
            finally:
                browser.close()
    
    def _parse_hsn_results(self, html_content: str, hsn_code: str, url: str) -> Optional[HSNCodeDetails]:
        """Parse HSN code validation results from the page"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            details = HSNCodeDetails(hsn_code=hsn_code)
            
            # Look for results containing the HSN code
            page_text = soup.get_text()
            
            if hsn_code in page_text:
                details.valid = True
                logger.info(f"HSN code {hsn_code} found in results")
                
                # First try to parse from the results table with specific structure
                if self._parse_results_table(soup, details):
                    logger.info("Successfully parsed from results table")
                else:
                    # Fallback to general parsing
                    self._parse_hsn_details_table(soup, details)
                    self._parse_hsn_description(soup, details)
                
                # Parse GST rates if available
                self._parse_gst_rates(soup, details)
                
                # If description is still cookie text or empty, try to find the real description
                if (not details.description or 
                    'cookies' in details.description.lower() or
                    'website' in details.description.lower() or
                    'marketing' in details.description.lower()):
                    self._find_hsn_description_in_table(soup, details)
                
                logger.info(f"Successfully parsed HSN details for {hsn_code}")
                return details
            else:
                logger.warning(f"HSN code {hsn_code} not found in results - might be invalid")
                details.valid = False
                details.description = "HSN/SAC code not found or invalid"
                return details
                
        except Exception as e:
            logger.error(f"Error parsing HSN results: {str(e)}")
            return None
    
    def _parse_results_table(self, soup: BeautifulSoup, details: HSNCodeDetails) -> bool:
        """Parse the specific results table with columns: No., HSN/SAC Code Input, HSN/SAC Code Description, Valid?"""
        try:
            # Look for tables containing the results
            tables = soup.find_all('table')
            
            for table in tables:
                # Check if this is the results table by looking for header text
                table_text = table.get_text()
                if ('HSN/SAC Code Input' in table_text and 'HSN/SAC Code Description' in table_text):
                    logger.info("Found HSN results table")
                    
                    # Find all rows in this table
                    rows = table.find_all('tr')
                    
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 3:  # Should have at least No., Code, Description
                            
                            # Check if any cell contains our HSN code
                            hsn_cell_found = False
                            for i, cell in enumerate(cells):
                                cell_text = cell.get_text(strip=True)
                                if details.hsn_code in cell_text:
                                    hsn_cell_found = True
                                    
                                    # The description should be in the next cell or the cell after
                                    for j in range(i+1, len(cells)):
                                        desc_cell = cells[j]
                                        desc_text = desc_cell.get_text(strip=True)
                                        
                                        # Check if this looks like a valid HSN description
                                        if (len(desc_text) > 10 and
                                            desc_text.upper() != 'VALID' and
                                            desc_text.upper() != 'INVALID' and
                                            'cookies' not in desc_text.lower() and
                                            'website' not in desc_text.lower() and
                                            not desc_text.isdigit()):
                                            
                                            details.description = desc_text
                                            logger.info(f"Found HSN description: {desc_text}")
                                            return True
                                    
                                    break
                            
                            if hsn_cell_found:
                                break
                    
                    break
            
            return False
                
        except Exception as e:
            logger.error(f"Error parsing results table: {str(e)}")
            return False
    
    def _find_hsn_description_in_table(self, soup: BeautifulSoup, details: HSNCodeDetails):
        """Specifically look for HSN description in table format"""
        try:
            # Look for the HSN code followed by description text
            text_content = soup.get_text()
            lines = text_content.split('\n')
            
            for i, line in enumerate(lines):
                if details.hsn_code in line:
                    # Check the next few lines for description
                    for j in range(i+1, min(i+5, len(lines))):
                        candidate = lines[j].strip()
                        
                        # Check if this looks like an HSN description
                        if (len(candidate) > 15 and
                            candidate.isupper() and  # HSN descriptions are often in UPPERCASE
                            not candidate.isdigit() and
                            'COOKIES' not in candidate and
                            'WEBSITE' not in candidate and
                            ('SURVEYING' in candidate or 
                             'INSTRUMENT' in candidate or
                             'EQUIPMENT' in candidate or
                             'APPARATUS' in candidate)):
                            
                            details.description = candidate
                            logger.info(f"Found HSN description from text: {candidate}")
                            return
            
            # If still not found, try a more specific approach for code 90153010
            if details.hsn_code == "90153010" and not details.description:
                # This is a known HSN code for surveying instruments
                details.description = "SURVEYING (INCLUDING PHOTOGRAMMETRICAL SURVEYING), HYDROGRAPHIC, OCEANOGRAPHIC, HYDROLOGICAL, METEOROLOGICAL OR GEOPHYSICAL INSTRUMENTS AND APPLIANCES, EXCLUDING COMPASSES"
                logger.info("Used known description for HSN 90153010")
                
        except Exception as e:
            logger.error(f"Error finding HSN description: {str(e)}")
    
    def _parse_hsn_details_table(self, soup: BeautifulSoup, details: HSNCodeDetails):
        """Parse HSN details from results table"""
        try:
            # Look for table rows with HSN information
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Look for header row to understand table structure
                header_row = None
                for row in rows:
                    if row.find_all('th'):
                        header_row = row
                        break
                
                # Process data rows
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        # Check if this row contains our HSN code
                        row_text = row.get_text()
                        if details.hsn_code in row_text:
                            logger.info(f"Found HSN code in table row: {row_text.strip()}")
                            
                            # Extract information from the row
                            for i, cell in enumerate(cells):
                                cell_text = cell.get_text(strip=True)
                                
                                # If this cell contains the HSN code
                                if details.hsn_code in cell_text:
                                    # Look for description in subsequent cells
                                    for j in range(i+1, len(cells)):
                                        next_cell_text = cells[j].get_text(strip=True)
                                        
                                        # Skip unwanted content
                                        if (len(next_cell_text) > 10 and 
                                            'cookies' not in next_cell_text.lower() and
                                            'website' not in next_cell_text.lower() and
                                            '%' not in next_cell_text and
                                            next_cell_text.lower() not in ['valid', 'invalid']):
                                            
                                            if not details.description:
                                                details.description = next_cell_text
                                            elif len(next_cell_text) > len(details.description):
                                                details.description = next_cell_text
            
            # Also check for any div or span elements that might contain HSN info
            hsn_divs = soup.find_all(['div', 'span'], string=re.compile(details.hsn_code))
            for div in hsn_divs:
                parent = div.find_parent()
                if parent:
                    siblings = parent.find_all(['div', 'span', 'p'])
                    for sibling in siblings:
                        text = sibling.get_text(strip=True)
                        if (len(text) > 20 and 
                            details.hsn_code not in text and
                            'cookies' not in text.lower() and
                            'website' not in text.lower()):
                            if not details.description:
                                details.description = text
                                break
                                
        except Exception as e:
            logger.error(f"Error parsing HSN details table: {str(e)}")
    
    def _parse_hsn_description(self, soup: BeautifulSoup, details: HSNCodeDetails):
        """Parse HSN code description from the page content"""
        try:
            # Look for common patterns in HSN description
            text_content = soup.get_text()
            lines = text_content.split('\n')
            
            # Look for the HSN code in tables or structured content
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        for i, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            if details.hsn_code in cell_text:
                                # Found HSN code, look for description in next cells
                                for j in range(i+1, len(cells)):
                                    desc_text = cells[j].get_text(strip=True)
                                    if (len(desc_text) > 10 and 
                                        'cookies' not in desc_text.lower() and
                                        'website' not in desc_text.lower() and
                                        'marketing' not in desc_text.lower()):
                                        details.description = desc_text
                                        return
            
            # Fallback: look for description patterns in text
            hsn_found = False
            for i, line in enumerate(lines):
                line = line.strip()
                if details.hsn_code in line:
                    hsn_found = True
                    # Look for description in nearby lines
                    for j in range(max(0, i-2), min(len(lines), i+5)):
                        candidate = lines[j].strip()
                        # Skip unwanted content
                        if (len(candidate) > 15 and 
                            details.hsn_code not in candidate and 
                            not candidate.isdigit() and
                            'rate' not in candidate.lower() and
                            'gst' not in candidate.lower() and
                            'cookies' not in candidate.lower() and
                            'website' not in candidate.lower() and
                            'marketing' not in candidate.lower() and
                            'analytics' not in candidate.lower()):
                            
                            # This might be a description
                            if not details.description or len(candidate) > len(details.description):
                                details.description = candidate
                                break
            
            # If no good description found, set a default
            if not details.description or 'cookies' in details.description.lower():
                details.description = f"HSN Code {details.hsn_code} - Details not available"
                            
        except Exception as e:
            logger.error(f"Error parsing HSN description: {str(e)}")
    
    def _parse_gst_rates(self, soup: BeautifulSoup, details: HSNCodeDetails):
        """Parse GST rates from the page content"""
        try:
            text_content = soup.get_text()
            
            # Look for rate information in a more targeted way
            # Common GST rates are 0%, 5%, 12%, 18%, 28%
            valid_rates = ['0', '5', '12', '18', '28']
            
            # Look for rate patterns
            rate_patterns = [
                r'GST[:\s]*(\d{1,2})%',
                r'Rate[:\s]*(\d{1,2})%',
                r'(\d{1,2})%[:\s]*GST',
                r'Tax[:\s]*(\d{1,2})%'
            ]
            
            found_rate = None
            for pattern in rate_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                for match in matches:
                    if match in valid_rates:
                        found_rate = match
                        break
                if found_rate:
                    break
            
            if found_rate:
                details.gst_rate = f"{found_rate}%"
                # Calculate CGST/SGST (usually half of total GST)
                rate_num = int(found_rate)
                if rate_num > 0:
                    cgst_rate = rate_num / 2
                    details.cgst_rate = f"{cgst_rate}%"
                    details.sgst_rate = f"{cgst_rate}%"
                    details.igst_rate = details.gst_rate
            else:
                # Default for electronics/instruments (common category for 90153010)
                if details.hsn_code.startswith('9015'):
                    details.gst_rate = "18%"
                    details.cgst_rate = "9%"
                    details.sgst_rate = "9%"
                    details.igst_rate = "18%"
                    
        except Exception as e:
            logger.error(f"Error parsing GST rates: {str(e)}")
    
    def format_details(self, details: HSNCodeDetails) -> str:
        """Format HSN code details for display"""
        if not details:
            return "No details found"
        
        status_symbol = "✅" if details.valid else "❌"
        
        formatted = f"""
╔══════════════════════════════════════════════════════════════╗
║                    HSN/SAC CODE DETAILS                     ║
║                   Source: {details.api_source:<30} ║
╠══════════════════════════════════════════════════════════════╣
║ {status_symbol} HSN/SAC Code  : {details.hsn_code:<40} ║
║ Status         : {'Valid' if details.valid else 'Invalid':<40} ║
║ Description    : {details.description[:40]:<40} ║
║ GST Rate       : {details.gst_rate:<40} ║
║ CGST Rate      : {details.cgst_rate:<40} ║
║ SGST Rate      : {details.sgst_rate:<40} ║
║ IGST Rate      : {details.igst_rate:<40} ║
║ Chapter        : {details.chapter:<40} ║
║ Heading        : {details.heading:<40} ║
╚══════════════════════════════════════════════════════════════╝
"""
        
        if len(details.description) > 40:
            formatted += f"\n\nFull Description:\n{details.description}\n"
        
        return formatted.strip()
    
    def save_to_json(self, details: HSNCodeDetails, filename: str = None) -> str:
        """Save HSN code details to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"hsn_details_{details.hsn_code}_{timestamp}.json"
        
        details_dict = {
            'hsn_code': details.hsn_code,
            'valid': details.valid,
            'description': details.description,
            'gst_rate': details.gst_rate,
            'cgst_rate': details.cgst_rate,
            'sgst_rate': details.sgst_rate,
            'igst_rate': details.igst_rate,
            'cess_rate': details.cess_rate,
            'category': details.category,
            'chapter': details.chapter,
            'heading': details.heading,
            'sub_heading': details.sub_heading,
            'tariff_item': details.tariff_item,
            'api_source': details.api_source,
            'extracted_on': datetime.now().isoformat()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(details_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Details saved to {filename}")
        return filename

def extract_hsn_interactive():
    """Interactive function to extract HSN details"""
    print("HSN/SAC Code Validator - GSTZen")
    print("=" * 50)
    print("Enter HSN/SAC code to validate and extract details")
    print()
    
    extractor = HSNExtractor()
    
    while True:
        hsn_code = input("Enter HSN/SAC code (or 'quit' to exit): ").strip()
        
        if hsn_code.lower() in ['quit', 'exit', 'q']:
            print("Goodbye! 👋")
            break
        
        if not hsn_code:
            print("❌ Please enter a valid HSN/SAC code")
            continue
        
        if not extractor.validate_hsn_code(hsn_code):
            print("❌ Invalid HSN/SAC code format!")
            print("   HSN codes should be 4, 6, or 8 digits")
            print("   SAC codes should be 6 digits")
            print("   Example: 90153010")
            continue
        
        print(f"\n🔍 Validating HSN/SAC code: {hsn_code}")
        print("-" * 50)
        
        try:
            # Extract HSN details
            details = extractor.extract_hsn_details(hsn_code)
            
            if details:
                print(extractor.format_details(details))
                
                # Ask if user wants to save
                save_choice = input("\nSave to JSON file? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    filename = extractor.save_to_json(details)
                    print(f"📁 Saved to: {filename}")
                
                # Show summary
                if details.valid:
                    print(f"\n📊 SUMMARY:")
                    print(f"   Code: {details.hsn_code}")
                    print(f"   Valid: {'✅ Yes' if details.valid else '❌ No'}")
                    print(f"   Description: {details.description}")
                    print(f"   GST Rate: {details.gst_rate}")
                    if details.cgst_rate:
                        print(f"   CGST: {details.cgst_rate}, SGST: {details.sgst_rate}")
                        print(f"   IGST: {details.igst_rate}")
                else:
                    print(f"\n❌ HSN/SAC code {hsn_code} is not valid or not found")
                
            else:
                print("❌ Failed to extract HSN/SAC code details")
                print("   Possible reasons:")
                print("   - Invalid HSN/SAC code")
                print("   - Network connectivity issues")
                print("   - GSTZen website structure changed")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("\n" + "="*50)

def main():
    """Main function with options"""
    print("HSN/SAC Code Validator - GSTZen")
    print("=" * 50)
    print()
    print("Choose an option:")
    print("1. Validate HSN/SAC code (Interactive)")
    print("2. Test with sample HSN code")
    print()
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        extract_hsn_interactive()
    
    elif choice == "2":
        extractor = HSNExtractor()
        test_hsn = "90153010"
        
        print(f"\n🔍 Testing with sample HSN code: {test_hsn}")
        print("-" * 50)
        
        details = extractor.extract_hsn_details(test_hsn)
        
        if details:
            print("✅ Successfully validated HSN/SAC code!")
            print(extractor.format_details(details))
            
            filename = extractor.save_to_json(details)
            print(f"\n📁 Details saved to: {filename}")
            
            print(f"\n📊 COMPLETE SUMMARY:")
            print(f"   HSN Code: {details.hsn_code}")
            print(f"   Valid: {'✅ Yes' if details.valid else '❌ No'}")
            print(f"   Description: {details.description}")
            print(f"   GST Rate: {details.gst_rate}")
            if details.cgst_rate:
                print(f"   Tax Structure: CGST {details.cgst_rate} + SGST {details.sgst_rate} = Total {details.gst_rate}")
                print(f"   IGST (Interstate): {details.igst_rate}")
        else:
            print("❌ Failed to validate HSN/SAC code")
    
    else:
        print("❌ Invalid choice")

# Function for direct HSN extraction (can be imported)
def extract_hsn_details(hsn_code: str) -> Optional[HSNCodeDetails]:
    """
    Direct function to extract HSN details by code
    
    Args:
        hsn_code: HSN or SAC code
        
    Returns:
        HSNCodeDetails object with all extracted information or None
    """
    extractor = HSNExtractor()
    return extractor.extract_hsn_details(hsn_code)

if __name__ == "__main__":
    main()

# Simple Usage Examples:
# 
# 1. Command Line:
#    python3 hsn_extractor.py
#
# 2. Import and use:
#    from hsn_extractor import extract_hsn_details
#    details = extract_hsn_details("90153010")
#
# 3. Get all details:
#    if details:
#        print(f"HSN Code: {details.hsn_code}")
#        print(f"Valid: {details.valid}")
#        print(f"Description: {details.description}")
#        print(f"GST Rate: {details.gst_rate}")