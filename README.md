# GST Taxpayer Details Extractor

A comprehensive Python tool to extract GST taxpayer details using browser automation with Playwright. The tool automates form interaction on GSTZen website to fetch complete taxpayer information including business details, registration info, and GST returns history.

## Features

- 🔍 **GSTIN Search**: Extract details by entering just the GSTIN number
- 🤖 **Browser Automation**: Uses Playwright for reliable form submission and navigation
- 📊 **Complete Data**: Comprehensive taxpayer information extraction
- 📄 **Multiple Formats**: Console display and JSON export
- ✅ **Input Validation**: GSTIN format validation
- 🔄 **Interactive Mode**: User-friendly command-line interface

## Quick Start

```bash
# Install dependencies
python3 -m pip install playwright beautifulsoup4
python3 -m playwright install chromium

# Run the tool
python3 gst_extractor.py

# Or extract programmatically
python3 -c "from gst_extractor import extract_gst_details; print(extract_gst_details('24AAXFA5297L1ZN'))"
```

## How It Works

1. **Browser Automation**: Launches Chromium browser using Playwright
2. **Form Interaction**: Navigates to GSTZen search page and fills GSTIN form
3. **Auto-Redirect**: Follows automatic redirect to taxpayer details page  
4. **Data Parsing**: Extracts comprehensive information using BeautifulSoup
5. **Results**: Returns structured data with all taxpayer details

## Installation

```bash
# Install Python packages
python3 -m pip install playwright beautifulsoup4

# Install browser binaries (one-time setup)
python3 -m playwright install chromium
```

## Usage

### Interactive Mode
```bash
python3 gst_extractor.py
```
Choose option 1 and enter any valid GSTIN.

### Programmatic Usage
```python
from gst_extractor import extract_gst_details

# Extract details
details = extract_gst_details("24AAXFA5297L1ZN")

if details:
    print(f"Company: {details.legal_name}")
    print(f"Status: {details.status}")
    print(f"State: {details.state}")
    print(f"Business: {details.nature_of_business}")
    print(f"Returns Filed: {len(details.recent_returns)} entries")
```

### Test with Sample Data
```bash
python3 gst_extractor.py
# Choose option 3 to test with sample GSTIN
```

## Extracted Information

The tool extracts comprehensive taxpayer details:

### Basic Information
- **GSTIN**: 15-digit GST identification number
- **Legal Name**: Official company/business name  
- **Trade Name**: Trading name (if different)
- **PAN Number**: Permanent Account Number
- **Status**: Registration status (Active/Cancelled)

### Registration Details
- **Registration Date**: GST registration date
- **Constitution**: Business constitution (Partnership, Company, etc.)
- **Taxpayer Type**: Regular/Composition/Other
- **Cancellation Date**: If applicable

### Location & Business
- **State**: Registered state
- **PIN Code**: Registration address PIN
- **Nature of Business**: Business activity details
- **State Jurisdiction**: State tax jurisdiction
- **Centre Jurisdiction**: Central tax jurisdiction  

### GST Returns History
- **Return Type**: GSTR-1, GSTR-3B, etc.
- **Period**: Tax period (month/year)
- **Filed Date**: Date of filing
- **Status**: Filing status

## Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║                    GST TAXPAYER DETAILS                     ║
║                   Source: GSTZen                         ║
╠══════════════════════════════════════════════════════════════╣
║ GST UIN          : 24AAXFA5297L1ZN                          ║
║ Legal Name       : ARIHANT TRADE WORLD                      ║
║ Trade Name       : ARIHANT TRADE WORD                       ║
║ PAN Number       : AAXFA5297L                               ║
║ Status           : Active                                   ║
║ Constitution     : Partnership                              ║
║ State            : Gujarat                                  ║
║ Business         : Retail Business, Wholesale Business      ║
║ Registration     : 01-Jul-2017                              ║
╚══════════════════════════════════════════════════════════════╝

Recent GST Returns Filed:
────────────────────────────────────────────────────────────
Return Type  Period          Filed Date      Status    
────────────────────────────────────────────────────────────
GSTR-3B      Sep 2019        07-Nov-2019     Filed     
GSTR-1       Aug 2019        04-Oct-2019     Filed     
GSTR-3B      Aug 2019        26-Sep-2019     Filed
```

## JSON Export

Data is automatically exported to JSON format:

```json
{
  "gstin": "24AAXFA5297L1ZN",
  "legal_name": "ARIHANT TRADE WORLD",
  "trade_name": "ARIHANT TRADE WORD", 
  "status": "Active",
  "constitution": "Partnership",
  "state": "Gujarat",
  "nature_of_business": "Retail Business, Wholesale Business",
  "recent_returns": [
    {
      "return_type": "GSTR-3B",
      "period": "Sep 2019", 
      "filed_date": "07-Nov-2019",
      "status": "Filed"
    }
  ],
  "extracted_on": "2024-01-01T10:00:00"
}
```

## Browser Automation

The tool uses Playwright for reliable automation:

- **Headless Browser**: Runs invisibly in background
- **Real Form Submission**: Handles dynamic content and redirects
- **Error Handling**: Robust error handling for network issues
- **Cross-Platform**: Works on macOS, Linux, Windows

## Dependencies

- **Python 3.7+**: Core language
- **Playwright**: Browser automation (`playwright`)
- **BeautifulSoup4**: HTML parsing (`beautifulsoup4`)  
- **Chromium**: Browser engine (installed via Playwright)

## Error Handling

The tool handles various error scenarios:

- **Invalid GSTIN Format**: Validates input format
- **Network Issues**: Timeout and retry logic
- **Missing Data**: Graceful handling of incomplete information
- **Website Changes**: Flexible selectors for form elements

## Technical Details

### Browser Automation Flow
1. Launch Chromium browser using Playwright
2. Navigate to GSTZen search page
3. Fill GSTIN in search form
4. Click search button  
5. Wait for automatic redirect
6. Extract data from taxpayer details page
7. Parse HTML using BeautifulSoup
8. Return structured data

### Data Sources
- **Primary**: GSTZen.in taxpayer search
- **Method**: Automated browser form submission
- **Parsing**: BeautifulSoup HTML extraction

## Troubleshooting

### Installation Issues
```bash
# If pip not found
python3 -m pip install playwright

# If browser installation fails  
python3 -m playwright install --help
```

### Runtime Issues
- **Timeout Errors**: Check internet connection
- **Form Element Not Found**: Website structure may have changed
- **Invalid GSTIN**: Verify 15-digit format

## File Structure

```
gst-extractor/
├── gst_extractor.py          # Main extractor script
├── README.md                 # Documentation 
└── gst_details_*.json        # Generated JSON files
```

## Contributing

This tool demonstrates:
- Browser automation with Playwright
- Form interaction and navigation
- HTML parsing and data extraction  
- Error handling and validation
- JSON data export

Perfect for learning web automation and data extraction techniques.

## Legal Notice

This tool is for educational and research purposes. Users are responsible for complying with website terms of service and applicable laws when using this tool.

---

**Made with ❤️ for the developer community**