# 📄➡️📊 PDF Invoice to JSON Converter

## 🚀 Quick Start

### 1. **Convert Any PDF Invoice to JSON**
```bash
python pdf_to_json.py your_invoice.pdf
```

### 2. **Test with Sample Data**
```bash
python test_pdf_to_json.py
```

## 🔧 How It Works

1. **OCR Processing**: Extracts text from PDF using Tesseract
2. **AI Analysis**: Gemini 2.0 Flash processes the text
3. **JSON Output**: Returns structured invoice data

## 📊 Output Format

The system extracts and structures:

```json
{
  "invoice_number": "INV-2024-0156",
  "invoice_date": "2024-03-15",
  "vendor": {
    "name": "Company Name",
    "address": "Full Address",
    "gstin": "GST Number",
    "phone": "Phone Number",
    "email": "Email"
  },
  "customer": {
    "name": "Customer Name",
    "address": "Customer Address",
    "gstin": "Customer GST"
  },
  "items": [
    {
      "description": "Item Description",
      "quantity": 1,
      "unit_price": 1000,
      "total_amount": 1000
    }
  ],
  "totals": {
    "subtotal": 1000,
    "cgst": 90,
    "sgst": 90,
    "grand_total": 1180
  }
}
```

## ✅ Features

- **OCR Text Extraction**: Handles printed and handwritten text
- **Image Preprocessing**: Enhances image quality for better OCR
- **AI-Powered Structuring**: Uses Gemini 2.0 Flash for accurate data extraction
- **GST Compliance**: Properly extracts Indian GST information
- **Multiple Formats**: Supports various invoice layouts
- **Error Handling**: Robust error handling and fallbacks

## 🔑 Setup Requirements

1. **API Key**: Add your Google API key to `.env` file:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

2. **Dependencies**: All packages are already installed
   - PyMuPDF (PDF processing)
   - Tesseract (OCR)
   - OpenCV (Image preprocessing)
   - Google Gemini AI
   - LangChain

## 📁 File Structure

- `pdf_to_json.py` - Main converter script
- `test_pdf_to_json.py` - Test with sample data
- `.env` - Your API key configuration
- Output files: `invoice_[filename]_[timestamp].json`

## 🎯 Usage Examples

### Process a Real PDF
```bash
# Convert invoice.pdf to JSON
python pdf_to_json.py invoice.pdf

# Output: invoice_invoice_20241107_143045.json
```

### Test the System
```bash
# Test with built-in sample data
python test_pdf_to_json.py

# Output: test_invoice_output.json
```

## 🔍 What Gets Extracted

- ✅ Invoice metadata (number, dates, PO number)
- ✅ Vendor information (name, address, GST, contact)
- ✅ Customer information (name, address, GST)
- ✅ Line items (description, quantity, rates, amounts)
- ✅ Tax calculations (CGST, SGST, IGST)
- ✅ Total amounts and currency
- ✅ Terms and conditions
- ✅ Payment information

## 🎉 Ready to Use!

Just drag and drop your PDF invoice and run:
```bash
python pdf_to_json.py your_invoice.pdf
```

The system will automatically:
1. 📄 Read your PDF
2. 👀 Extract text using OCR
3. 🤖 Process with Gemini AI
4. 💾 Save structured JSON
5. 📊 Show summary