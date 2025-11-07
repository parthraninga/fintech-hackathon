# 📄 PDF Invoice Extractor

A comprehensive Python tool that extracts structured data from PDF invoices using OCR (Tesseract) and AI processing (Google Gemini). Capable of handling both printed text and handwritten content with advanced image preprocessing.

## 🚀 Features

- **OCR Text Extraction**: Uses Tesseract OCR with advanced image preprocessing
- **Handwritten Text Support**: Handles invoices with handwritten annotations
- **AI-Powered Structuring**: Google Gemini AI structures raw OCR text into organized data
- **Pydantic Data Models**: Type-safe, validated data structures
- **Multi-format Support**: Processes various PDF invoice formats
- **Error Handling**: Comprehensive error handling and logging
- **JSON Export**: Structured data exported in JSON format

## 📋 Prerequisites

### System Requirements
- Python 3.7+
- Tesseract OCR (installed via Homebrew on macOS)
- Google API Key for Gemini AI

### Dependencies
```bash
pip install PyMuPDF opencv-python pytesseract langchain-google-genai pydantic pillow
```

### Tesseract Installation (macOS)
```bash
brew install tesseract
```

## 🔧 Setup

1. **Clone or download the files**:
   - `invoice_extractor.py` - Main extraction class
   - `test_invoice_processor.py` - Test script

2. **Set up Google API Key**:
   ```bash
   export GOOGLE_API_KEY="your_google_api_key_here"
   ```

3. **Verify Tesseract installation**:
   ```bash
   tesseract --version
   ```

## 🎯 Usage

### Basic Usage

```python
from invoice_extractor import InvoiceExtractor
import os

# Initialize with Google API key
api_key = os.getenv('GOOGLE_API_KEY')
extractor = InvoiceExtractor(api_key=api_key)

# Extract invoice data
result = extractor.extract_invoice('path/to/invoice.pdf')

# Access structured data
print(f"Vendor: {result.vendor_info.name}")
print(f"Invoice Number: {result.invoice_number}")
print(f"Total Amount: {result.totals.grand_total}")

# Save to JSON
extractor.save_to_json(result, 'invoice_data.json')
```

### Test the System

```bash
python test_invoice_processor.py
```

## 📊 Data Structure

The extractor returns structured data with these components:

### VendorInfo
- `name`: Company name
- `address`: Complete address
- `gstin`: GST identification number
- `phone`: Contact number
- `email`: Email address

### CustomerInfo
- `name`: Customer/client name
- `address`: Billing address
- `gstin`: Customer's GST number

### InvoiceItem
- `description`: Item/service description
- `quantity`: Quantity ordered
- `unit_price`: Price per unit
- `total_amount`: Line total

### TotalAmounts
- `subtotal`: Amount before taxes
- `cgst`: Central GST amount
- `sgst`: State GST amount
- `igst`: Integrated GST amount
- `other_charges`: Additional charges
- `grand_total`: Final amount

### StructuredInvoice (Complete Model)
- `invoice_number`: Unique invoice identifier
- `invoice_date`: Date of invoice
- `due_date`: Payment due date
- `vendor_info`: Vendor details
- `customer_info`: Customer details
- `items`: List of invoice items
- `totals`: Amount calculations
- `terms_conditions`: Payment terms
- `amount_in_words`: Amount spelled out

## 🔍 How It Works

1. **PDF Processing**: Converts PDF pages to images using PyMuPDF
2. **Image Preprocessing**: Enhances image quality using OpenCV:
   - Grayscale conversion
   - Gaussian blur
   - Thresholding for better OCR
3. **OCR Extraction**: Uses Tesseract to extract all text (printed + handwritten)
4. **AI Processing**: Google Gemini structures the raw text into organized data
5. **Data Validation**: Pydantic models ensure data integrity
6. **JSON Export**: Saves structured data with timestamps

## 🛠️ Advanced Configuration

### Image Preprocessing Parameters

You can customize OCR preprocessing in the `_preprocess_image()` method:

```python
# Adjust for different image qualities
blur_kernel = (5, 5)  # Gaussian blur kernel size
threshold_type = cv2.THRESH_BINARY + cv2.THRESH_OTSU  # Thresholding method
```

### Gemini AI Prompt

The AI prompt in `_process_with_ai()` can be customized for specific invoice formats or additional fields.

## 📝 Example Output

```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-03-15",
  "vendor_info": {
    "name": "ABC Technology Solutions Pvt Ltd",
    "address": "123 Tech Park, Sector 5, Bangalore, Karnataka - 560001",
    "gstin": "29AABCT1234M1Z5",
    "phone": "+91-80-12345678"
  },
  "customer_info": {
    "name": "XYZ Corporation",
    "address": "456 Business Plaza, Mumbai, Maharashtra - 400001",
    "gstin": "27AAXYZ9876N1W2"
  },
  "items": [
    {
      "description": "Web Development Services",
      "quantity": 1,
      "unit_price": 50000,
      "total_amount": 50000
    }
  ],
  "totals": {
    "subtotal": 95000,
    "cgst": 8550,
    "sgst": 8550,
    "grand_total": 112100
  }
}
```

## 🔗 Integration with Other Tools

This invoice extractor complements the other tools in this workspace:

- **GST Extractor** (`gst_extractor.py`): Verify vendor/customer GST details
- **HSN Extractor** (`hsn_extractor.py`): Validate HSN codes from invoices

## 🐛 Troubleshooting

### Common Issues

1. **"tesseract not found"**:
   ```bash
   brew install tesseract
   ```

2. **Poor OCR results**:
   - Ensure good PDF quality
   - Adjust preprocessing parameters
   - Try different image enhancement techniques

3. **AI processing errors**:
   - Verify Google API key is set
   - Check API quotas and billing
   - Ensure proper internet connectivity

4. **Memory issues with large PDFs**:
   - Process pages individually
   - Reduce image resolution if needed

### Debugging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎓 Technical Details

### OCR Engine
- **Tesseract 5.5.1**: Latest version with improved accuracy
- **Language Support**: English (eng) by default
- **Page Segmentation**: Optimized for invoice layouts

### AI Processing
- **Model**: Google Gemini Pro via LangChain
- **Token Limits**: Handles large invoices efficiently
- **Structured Output**: Uses Pydantic for type safety

### Image Processing
- **OpenCV**: Advanced image enhancement
- **Format Support**: PNG, JPEG, TIFF from PDF conversion
- **Quality Enhancement**: Adaptive thresholding and noise reduction

## 🤝 Contributing

Feel free to enhance the tool by:
- Adding support for more languages
- Improving OCR preprocessing
- Extending the Pydantic models
- Adding more invoice formats

## 📄 License

This tool is part of the GST/Invoice processing suite and follows the same licensing terms.