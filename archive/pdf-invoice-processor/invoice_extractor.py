"""
Invoice OCR and Structure Extractor using Tesseract + Google Gemini

This module extracts text from PDF invoices (including handwritten content) using Tesseract OCR,
then uses Google Gemini via LangChain to structure the extracted text into a proper invoice format.

Features:
- Handle both scanned and text-based PDFs
- OCR with preprocessing for handwritten content
- Google Gemini integration for intelligent structuring
- Comprehensive invoice field extraction
- JSON export with complete invoice data

Quick Usage:
    from invoice_extractor import extract_invoice_from_pdf
    
    result = extract_invoice_from_pdf("invoice.pdf")
    if result:
        print(f"Invoice from: {result['vendor']['name']}")
        print(f"Total: {result['totals']['grand_total']}")

Interactive Usage:
    python3 invoice_extractor.py
"""

import os
import json
import io
import cv2
import numpy as np
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from typing import Dict, Optional, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging
import re

# LangChain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for structured output
class VendorInfo(BaseModel):
    name: str = Field(description="Vendor/Company name")
    address: str = Field(description="Complete vendor address")
    phone: str = Field(default="", description="Phone number")
    email: str = Field(default="", description="Email address")
    gst_number: str = Field(default="", description="GST/Tax registration number")
    pan_number: str = Field(default="", description="PAN number")
    website: str = Field(default="", description="Website URL")

class CustomerInfo(BaseModel):
    name: str = Field(description="Customer/Buyer name")
    address: str = Field(description="Complete customer address")
    phone: str = Field(default="", description="Phone number")
    email: str = Field(default="", description="Email address")
    gst_number: str = Field(default="", description="Customer GST number")

class InvoiceItem(BaseModel):
    item_number: str = Field(default="", description="Item/Product number or SKU")
    description: str = Field(description="Item description")
    hsn_code: str = Field(default="", description="HSN/SAC code")
    quantity: float = Field(description="Quantity")
    unit: str = Field(default="", description="Unit of measurement")
    rate: float = Field(description="Rate per unit")
    discount: float = Field(default=0.0, description="Discount amount")
    taxable_amount: float = Field(description="Taxable amount")
    cgst_rate: float = Field(default=0.0, description="CGST rate percentage")
    cgst_amount: float = Field(default=0.0, description="CGST amount")
    sgst_rate: float = Field(default=0.0, description="SGST rate percentage") 
    sgst_amount: float = Field(default=0.0, description="SGST amount")
    igst_rate: float = Field(default=0.0, description="IGST rate percentage")
    igst_amount: float = Field(default=0.0, description="IGST amount")
    total_amount: float = Field(description="Total amount for this item")

class PaymentInfo(BaseModel):
    payment_method: str = Field(default="", description="Payment method (cash, card, bank transfer, etc.)")
    payment_terms: str = Field(default="", description="Payment terms")
    bank_details: str = Field(default="", description="Bank account details")
    payment_status: str = Field(default="", description="Payment status (paid, pending, etc.)")

class TotalAmounts(BaseModel):
    subtotal: float = Field(description="Subtotal before taxes")
    total_discount: float = Field(default=0.0, description="Total discount amount")
    total_cgst: float = Field(default=0.0, description="Total CGST amount")
    total_sgst: float = Field(default=0.0, description="Total SGST amount") 
    total_igst: float = Field(default=0.0, description="Total IGST amount")
    total_tax: float = Field(description="Total tax amount")
    round_off: float = Field(default=0.0, description="Round off amount")
    grand_total: float = Field(description="Final grand total")
    amount_in_words: str = Field(default="", description="Amount in words")

class InvoiceStructure(BaseModel):
    invoice_number: str = Field(description="Invoice number")
    invoice_date: str = Field(description="Invoice date")
    due_date: str = Field(default="", description="Payment due date")
    purchase_order_number: str = Field(default="", description="Purchase order number")
    vendor: VendorInfo = Field(description="Vendor/Seller information")
    customer: CustomerInfo = Field(description="Customer/Buyer information")
    items: List[InvoiceItem] = Field(description="List of invoice items")
    totals: TotalAmounts = Field(description="Total amounts and calculations")
    payment: PaymentInfo = Field(description="Payment information")
    notes: str = Field(default="", description="Additional notes or terms")
    currency: str = Field(default="INR", description="Currency code")

@dataclass
class OCRResult:
    """Data class to store OCR extraction results"""
    raw_text: str
    confidence: float
    preprocessed_image_path: str = ""
    extraction_method: str = "tesseract"

class InvoiceExtractor:
    """Invoice OCR and Structure Extractor using Tesseract + Google Gemini"""
    
    def __init__(self, google_api_key: Optional[str] = None):
        """
        Initialize the Invoice Extractor
        
        Args:
            google_api_key: Google API key for Gemini AI. If None, only OCR will work.
        """
        self.google_api_key = google_api_key
        self.logger = self._setup_logging()
        
        # Initialize Gemini AI if API key is provided
        if self.google_api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    google_api_key=self.google_api_key,
                    temperature=0.1
                )
                self.logger.info("✅ Gemini AI initialized successfully")
                
                # Initialize parser and prompt template for AI processing
                from langchain.output_parsers.pydantic import PydanticOutputParser
                from langchain.prompts import PromptTemplate
                
                self.parser = PydanticOutputParser(pydantic_object=InvoiceStructure)
                self.prompt_template = PromptTemplate(
                    template=self._get_ai_prompt_template(),
                    input_variables=["ocr_text", "format_instructions"]
                )
                
            except Exception as e:
                self.logger.warning(f"⚠️  Failed to initialize Gemini AI: {e}")
                self.llm = None
                self.parser = None
                self.prompt_template = None
        else:
            self.llm = None
            self.parser = None
            self.prompt_template = None
            self.logger.info("⚠️  No Google API key provided. OCR-only mode.")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the invoice extractor"""
        logger = logging.getLogger(f"{__name__}.InvoiceExtractor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _get_ai_prompt_template(self) -> str:
        """Get the AI prompt template for invoice processing"""
        return """
You are an expert invoice processing AI. Extract and structure the following OCR text into a complete invoice format.

OCR Text:
{ocr_text}

Instructions:
1. Extract all vendor/company details (name, address, GSTIN, phone, email)
2. Extract customer/billing details (name, address, GSTIN)
3. Extract invoice metadata (number, date, due date, PO number)
4. Extract all invoice items with quantities, rates, and amounts
5. Extract all totals, taxes (CGST, SGST, IGST), and final amounts
6. Extract payment terms and conditions
7. If any field is not found, use appropriate defaults
8. For GST numbers, ensure proper format: XXAAAXXXXXXXX
9. For dates, use YYYY-MM-DD format

{format_instructions}

Output the structured data exactly as specified in the format instructions.
"""
    
    def extract_invoice_from_pdf(self, pdf_path: str, output_dir: str = "output") -> Optional[Dict[str, Any]]:
        """
        Extract and structure invoice data from PDF
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save output files
            
        Returns:
            Structured invoice data as dictionary
        """
        try:
            logger.info(f"Processing PDF: {pdf_path}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Step 1: Convert PDF to images and extract text
            ocr_result = self._extract_text_from_pdf(pdf_path, output_dir)
            
            if not ocr_result.raw_text.strip():
                logger.error("No text extracted from PDF")
                return None
            
            # Step 2: Structure the text using Gemini
            structured_data = self._structure_invoice_with_gemini(ocr_result.raw_text)
            
            if not structured_data:
                logger.error("Failed to structure invoice data")
                return None
            
            # Step 3: Save results
            result = {
                'structured_invoice': structured_data,
                'ocr_metadata': {
                    'raw_text': ocr_result.raw_text,
                    'confidence': ocr_result.confidence,
                    'extraction_method': ocr_result.extraction_method,
                    'preprocessed_image': ocr_result.preprocessed_image_path,
                    'processed_date': datetime.now().isoformat()
                }
            }
            
            # Save to JSON
            output_file = os.path.join(output_dir, f"invoice_structured_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            self._save_to_json(result, output_file)
            
            logger.info(f"Invoice processing completed. Results saved to: {output_file}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing invoice: {str(e)}")
            return None
    
    def _extract_text_from_pdf(self, pdf_path: str, output_dir: str) -> OCRResult:
        """Extract text from PDF using multiple approaches"""
        try:
            # Try text extraction first (for text-based PDFs)
            text_content = self._extract_text_from_text_pdf(pdf_path)
            
            if text_content and len(text_content.strip()) > 100:
                logger.info("Extracted text directly from PDF")
                return OCRResult(
                    raw_text=text_content,
                    confidence=1.0,
                    extraction_method="direct_text"
                )
            
            # If direct text extraction fails or yields little content, use OCR
            logger.info("Using OCR for text extraction")
            return self._extract_text_with_ocr(pdf_path, output_dir)
            
        except Exception as e:
            logger.error(f"Error in text extraction: {str(e)}")
            return OCRResult(raw_text="", confidence=0.0)
    
    def _extract_text_from_text_pdf(self, pdf_path: str) -> str:
        """Extract text directly from text-based PDF"""
        try:
            doc = fitz.open(pdf_path)
            text_content = ""
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text_content += page.get_text() + "\n"
            
            doc.close()
            return text_content.strip()
            
        except Exception as e:
            logger.warning(f"Direct text extraction failed: {str(e)}")
            return ""
    
    def _extract_text_with_ocr(self, pdf_path: str, output_dir: str) -> OCRResult:
        """Extract text using OCR with image preprocessing"""
        try:
            # Convert PDF pages to images
            doc = fitz.open(pdf_path)
            all_text = ""
            total_confidence = 0
            page_count = 0
            
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Convert page to image
                mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # Convert to PIL Image
                image = Image.open(io.BytesIO(img_data))
                
                # Preprocess image for better OCR
                processed_image = self._preprocess_image_for_ocr(image)
                
                # Save preprocessed image
                processed_image_path = os.path.join(output_dir, f"processed_page_{page_num + 1}.png")
                processed_image.save(processed_image_path)
                
                # Perform OCR
                ocr_data = pytesseract.image_to_data(processed_image, output_type=pytesseract.Output.DICT)
                page_text = pytesseract.image_to_string(processed_image)
                
                # Calculate confidence
                confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                page_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                all_text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
                total_confidence += page_confidence
                page_count += 1
                
                logger.info(f"Processed page {page_num + 1} with confidence: {page_confidence:.1f}%")
            
            doc.close()
            
            avg_confidence = total_confidence / page_count if page_count > 0 else 0
            
            return OCRResult(
                raw_text=all_text,
                confidence=avg_confidence,
                preprocessed_image_path=processed_image_path if page_count > 0 else "",
                extraction_method="tesseract_ocr"
            )
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return OCRResult(raw_text="", confidence=0.0)
    
    def _preprocess_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR accuracy, especially for handwritten content"""
        try:
            # Convert PIL to OpenCV
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_array
            
            # Apply preprocessing techniques
            # 1. Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(gray, (1, 1), 0)
            
            # 2. Adaptive thresholding for better contrast
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # 3. Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # 4. Sharpen the image
            kernel_sharpen = np.array([[-1,-1,-1],
                                     [-1, 9,-1],
                                     [-1,-1,-1]])
            sharpened = cv2.filter2D(cleaned, -1, kernel_sharpen)
            
            # Convert back to PIL
            processed_image = Image.fromarray(sharpened)
            
            return processed_image
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {str(e)}")
            return image
    
    def _structure_invoice_with_gemini(self, ocr_text: str) -> Optional[Dict[str, Any]]:
        """Structure the OCR text using Google Gemini"""
        if not self.llm:
            logger.warning("⚠️  Gemini AI not available. Cannot structure invoice data.")
            return None
            
        try:
            logger.info("Structuring invoice data with Google Gemini...")
            
            # Prepare the prompt
            format_instructions = self.parser.get_format_instructions()
            prompt = self.prompt_template.format(
                ocr_text=ocr_text,
                format_instructions=format_instructions
            )
            
            # Create messages
            messages = [
                SystemMessage(content="You are an expert invoice processing AI specializing in extracting and structuring invoice data from OCR text."),
                HumanMessage(content=prompt)
            ]
            
            # Get response from Gemini
            response = self.llm(messages)
            
            # Parse the response
            try:
                structured_data = self.parser.parse(response.content)
                return structured_data.dict()
            except Exception as parse_error:
                logger.error(f"Failed to parse Gemini response: {parse_error}")
                
                # Fallback: try to extract JSON manually
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except:
                        pass
                
                # If all parsing fails, return raw response for debugging
                logger.warning("Returning raw response due to parsing failure")
                return {"raw_gemini_response": response.content}
            
        except Exception as e:
            logger.error(f"Gemini structuring failed: {str(e)}")
            return None
    
    def _save_to_json(self, data: Dict[str, Any], filepath: str):
        """Save structured data to JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"Results saved to: {filepath}")
        except Exception as e:
            logger.error(f"Failed to save JSON: {str(e)}")
    
    def format_invoice_summary(self, structured_data: Dict[str, Any]) -> str:
        """Format invoice data for display"""
        try:
            invoice = structured_data.get('structured_invoice', {})
            
            summary = f"""
╔══════════════════════════════════════════════════════════════╗
║                      INVOICE SUMMARY                         ║
╠══════════════════════════════════════════════════════════════╣
║ Invoice #        : {invoice.get('invoice_number', 'N/A'):<39} ║
║ Date             : {invoice.get('invoice_date', 'N/A'):<39} ║
║ Due Date         : {invoice.get('due_date', 'N/A'):<39} ║
╠══════════════════════════════════════════════════════════════╣
║ Vendor           : {invoice.get('vendor', {}).get('name', 'N/A')[:39]:<39} ║
║ Customer         : {invoice.get('customer', {}).get('name', 'N/A')[:39]:<39} ║
╠══════════════════════════════════════════════════════════════╣
║ Items            : {len(invoice.get('items', [])):<39} ║
║ Subtotal         : {invoice.get('totals', {}).get('subtotal', 0):<39} ║
║ Total Tax        : {invoice.get('totals', {}).get('total_tax', 0):<39} ║
║ Grand Total      : {invoice.get('totals', {}).get('grand_total', 0):<39} ║
║ Currency         : {invoice.get('currency', 'N/A'):<39} ║
╚══════════════════════════════════════════════════════════════╝
"""
            
            # Add items summary
            items = invoice.get('items', [])
            if items:
                summary += "\n\nITEMS BREAKDOWN:\n"
                summary += "─" * 60 + "\n"
                for i, item in enumerate(items[:5], 1):  # Show first 5 items
                    summary += f"{i}. {item.get('description', 'N/A')[:30]:<30} "
                    summary += f"₹{item.get('total_amount', 0):>10}\n"
                
                if len(items) > 5:
                    summary += f"... and {len(items) - 5} more items\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error formatting summary: {str(e)}")
            return "Error formatting invoice summary"

def extract_invoice_from_pdf(pdf_path: str, gemini_api_key: str = None, output_dir: str = "output") -> Optional[Dict[str, Any]]:
    """
    Direct function to extract invoice from PDF
    
    Args:
        pdf_path: Path to PDF file
        gemini_api_key: Google Gemini API key
        output_dir: Output directory
        
    Returns:
        Structured invoice data
    """
    try:
        extractor = InvoiceExtractor(gemini_api_key)
        return extractor.extract_invoice_from_pdf(pdf_path, output_dir)
    except Exception as e:
        logger.error(f"Invoice extraction failed: {str(e)}")
        return None

def main():
    """Main function for interactive usage"""
    print("Invoice OCR and Structure Extractor")
    print("=" * 50)
    print()
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ Google Gemini API key not found!")
        print("   Please set the GEMINI_API_KEY environment variable")
        print("   Example: export GEMINI_API_KEY='your-api-key'")
        return
    
    print("Choose an option:")
    print("1. Process a PDF invoice")
    print("2. Test with sample (if available)")
    print()
    
    choice = input("Enter choice (1-2): ").strip()
    
    if choice == "1":
        pdf_path = input("Enter path to PDF file: ").strip()
        
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            return
        
        print(f"\n🔍 Processing invoice: {pdf_path}")
        print("-" * 50)
        
        try:
            extractor = InvoiceExtractor(api_key)
            result = extractor.extract_invoice_from_pdf(pdf_path)
            
            if result:
                print("✅ Invoice processed successfully!")
                print(extractor.format_invoice_summary(result))
                
                # Show OCR confidence
                ocr_meta = result.get('ocr_metadata', {})
                print(f"\n📊 OCR Confidence: {ocr_meta.get('confidence', 0):.1f}%")
                print(f"📊 Extraction Method: {ocr_meta.get('extraction_method', 'N/A')}")
                print(f"📊 Items Found: {len(result.get('structured_invoice', {}).get('items', []))}")
                
            else:
                print("❌ Failed to process invoice")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    elif choice == "2":
        print("Sample processing not implemented yet")
        print("Please provide a PDF file using option 1")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()

# Usage Examples:
#
# 1. Command Line:
#    export GEMINI_API_KEY='your-api-key'
#    python3 invoice_extractor.py
#
# 2. Import and use:
#    from invoice_extractor import extract_invoice_from_pdf
#    result = extract_invoice_from_pdf("invoice.pdf", "your-api-key")
#
# 3. Get structured data:
#    if result:
#        invoice = result['structured_invoice']
#        print(f"Vendor: {invoice['vendor']['name']}")
#        print(f"Total: {invoice['totals']['grand_total']}")