# HSN/SAC Code Validator and Extractor

A Python tool to validate and extract comprehensive HSN/SAC code details using browser automation with Playwright. The tool automates the HSN code validation form on GSTZen website to fetch complete code information including descriptions and GST rates.

## Features

- 🔍 **HSN/SAC Validation**: Validate HSN and SAC codes with format checking
- 🤖 **Browser Automation**: Uses Playwright for reliable form submission
- 📊 **Complete Details**: Extract code descriptions, GST rates, and tax structure
- ✅ **Validation**: Verify if HSN/SAC codes are valid
- 📄 **JSON Export**: Save results with timestamps
- 🔄 **Multiple Modes**: Interactive CLI and programmatic usage

## Quick Start

```bash
# Install dependencies (if not already installed)
python3 -m pip install playwright beautifulsoup4
python3 -m playwright install chromium

# Run the HSN validator
python3 hsn_extractor.py

# Or extract programmatically
python3 -c "from hsn_extractor import extract_hsn_details; print(extract_hsn_details('90153010'))"
```

## Usage

### Interactive Mode
```bash
python3 hsn_extractor.py
# Choose option 1 and enter any HSN/SAC code
```

### Programmatic Usage
```python
from hsn_extractor import extract_hsn_details

# Extract HSN code details
details = extract_hsn_details("90153010")

if details:
    print(f"HSN Code: {details.hsn_code}")
    print(f"Valid: {details.valid}")
    print(f"Description: {details.description}")
    print(f"GST Rate: {details.gst_rate}")
    print(f"CGST: {details.cgst_rate}, SGST: {details.sgst_rate}")
```

### Test Mode
```bash
python3 hsn_extractor.py
# Choose option 2 to test with sample HSN code 90153010
```

## Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║                    HSN/SAC CODE DETAILS                     ║
║                   Source: GSTZen                         ║
╠══════════════════════════════════════════════════════════════╣
║ ✅ HSN/SAC Code  : 90153010                                 ║
║ Status         : Valid                                    ║
║ Description    : SURVEYING (INCLUDING PHOTOGRAMMETRICAL S ║
║ GST Rate       : 18%                                      ║
║ CGST Rate      : 9%                                       ║
║ SGST Rate      : 9%                                       ║
║ IGST Rate      : 18%                                      ║
╚══════════════════════════════════════════════════════════════╝

Full Description:
SURVEYING (INCLUDING PHOTOGRAMMETRICAL SURVEYING)…
```

## JSON Export

```json
{
  "hsn_code": "90153010",
  "valid": true,
  "description": "SURVEYING (INCLUDING PHOTOGRAMMETRICAL SURVEYING)…",
  "gst_rate": "18%",
  "cgst_rate": "9%",
  "sgst_rate": "9%",
  "igst_rate": "18%",
  "api_source": "GSTZen",
  "extracted_on": "2025-11-07T12:44:19.040181"
}
```

## How It Works

1. **Form Automation**: Navigates to GSTZen HSN validator page
2. **Code Input**: Fills HSN/SAC code in the textarea field
3. **Form Submission**: Clicks the validation button
4. **Results Parsing**: Extracts data from the results table
5. **GST Rate Assignment**: Applies appropriate tax rates based on code category

## HSN/SAC Code Format

- **HSN Codes**: 4, 6, or 8 digits (Harmonized System of Nomenclature)
- **SAC Codes**: 6 digits (Services Accounting Codes)
- **Examples**: 90153010, 123456, 12345678

## Dependencies

- **Python 3.7+**: Core language
- **Playwright**: Browser automation
- **BeautifulSoup4**: HTML parsing
- **Chromium**: Browser engine (via Playwright)

## Data Extracted

- **HSN/SAC Code**: The input code
- **Validation Status**: Whether the code is valid
- **Description**: Full description of goods/services
- **GST Rates**: Total GST, CGST, SGST, IGST rates
- **Tax Structure**: Breakdown of tax components

## Browser Automation

The tool uses Playwright for reliable automation:
- Handles dynamic content loading
- Parses results table accurately
- Manages form submissions and redirects
- Runs in headless mode for efficiency

## Error Handling

- **Invalid Format**: Validates input before processing
- **Code Not Found**: Returns appropriate error message
- **Network Issues**: Handles timeouts and connectivity problems
- **Parsing Errors**: Graceful failure with detailed logging

## Technical Details

### Automation Flow
1. Launch Chromium browser with Playwright
2. Navigate to HSN validator page
3. Scroll to form location
4. Fill HSN/SAC code in textarea field
5. Submit form and wait for results
6. Parse results table for code details
7. Extract description and validation status
8. Apply GST rates based on code category

### Data Sources
- **Primary**: GSTZen HSN/SAC validator
- **Method**: Automated browser form submission
- **Parsing**: BeautifulSoup HTML table extraction

## File Structure

```
gst-extractor/
├── hsn_extractor.py          # HSN/SAC code validator
├── hsn_details_*.json        # Generated JSON files
└── README_HSN.md            # This documentation
```

## Example Codes to Test

- **90153010**: Surveying instruments (18% GST)
- **84713000**: Computers and laptops (18% GST)
- **25232900**: Portland cement (28% GST)
- **10059000**: Maize/corn (0% GST)

## Contributing

This tool demonstrates:
- Browser automation with Playwright
- HTML table parsing and data extraction
- Form interaction and validation
- Tax rate calculation and assignment

Perfect for learning web scraping and automation techniques for tax/compliance data.

## Legal Notice

This tool is for educational and research purposes. Users are responsible for complying with website terms of service and applicable laws.

---

**Made with ❤️ for tax compliance and automation**