# 📁 PDF Invoice Processor Archive

This folder contains all files related to the PDF Invoice to JSON conversion system that was developed.

## 📄 Files Archived

### Main Scripts
- `pdf_to_json.py` - Main PDF to JSON converter script
- `invoice_extractor.py` - Original comprehensive invoice extractor class
- `test_pdf_to_json.py` - Test script for PDF to JSON conversion
- `test_invoice_processor.py` - Test script for invoice extractor

### Documentation
- `README_INVOICE.md` - Comprehensive documentation for invoice extractor
- `README_PDF_TO_JSON.md` - Quick start guide for PDF to JSON converter

### Output Files
- `*.json` - Generated JSON files from testing

## 🚀 How to Use (If Needed)

If you need to use these scripts again:

1. **Copy back to main folder**:
   ```bash
   cp archive/pdf-invoice-processor/pdf_to_json.py .
   ```

2. **Run with your PDF**:
   ```bash
   python pdf_to_json.py your_invoice.pdf
   ```

## ⚙️ System Capabilities

The archived system could:
- ✅ Extract text from PDF using OCR (Tesseract)
- ✅ Process with Google Gemini AI
- ✅ Return structured JSON with invoice data
- ✅ Handle vendor, customer, items, taxes, totals
- ✅ Process both printed and handwritten content
- ✅ Strict mode: No mock data, only actual extracted data

## 📅 Archived Date
November 7, 2025

## 🔧 Dependencies
- PyMuPDF, Tesseract OCR, OpenCV, LangChain, Google Gemini AI
- All were installed and working at time of archival