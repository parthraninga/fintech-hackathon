#!/usr/bin/env python3
"""
PDF Invoice to JSON Converter

This script:
1. Takes a PDF file as input
2. Performs OCR to extract text
3. Sends text to Gemini AI
4. Returns structured JSON
"""

import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import cv2
import numpy as np
import json
import os
import sys
import io
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

class PDFToJSON:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("❌ GOOGLE_API_KEY not found in .env file")
        
        # Initialize Gemini
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=self.api_key,
                temperature=0.1
            )
            print("✅ Gemini AI initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize Gemini: {e}")
            sys.exit(1)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        print(f"📄 Processing PDF: {pdf_path}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Open PDF
        doc = fitz.open(pdf_path)
        all_text = ""
        
        for page_num in range(len(doc)):
            print(f"📖 Processing page {page_num + 1}/{len(doc)}")
            page = doc.load_page(page_num)
            
            # Convert page to image
            mat = fitz.Matrix(2.0, 2.0)  # High resolution
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            
            # Convert to PIL Image
            image = Image.open(io.BytesIO(img_data))
            
            # Preprocess image for better OCR
            processed_image = self._preprocess_for_ocr(image)
            
            # Perform OCR
            text = pytesseract.image_to_string(processed_image, lang='eng')
            all_text += f"\n--- Page {page_num + 1} ---\n{text}\n"
        
        doc.close()
        print(f"✅ OCR completed. Extracted {len(all_text)} characters")
        return all_text.strip()
    
    def _preprocess_for_ocr(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert PIL to OpenCV
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Convert to grayscale
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply threshold to get better contrast
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Convert back to PIL
        return Image.fromarray(thresh)
    
    def convert_to_json(self, text: str) -> dict:
        """Convert OCR text to structured JSON using Gemini"""
        print("🤖 Converting to JSON using Gemini AI...")
        
        system_prompt = """You are an expert invoice processing AI. Convert the given OCR text into a structured JSON format.

Extract the following information and return ONLY a valid JSON object:

{
  "invoice_number": "string",
  "invoice_date": "YYYY-MM-DD",
  "due_date": "YYYY-MM-DD",
  "vendor": {
    "name": "string",
    "address": "string",
    "gstin": "string",
    "phone": "string",
    "email": "string"
  },
  "customer": {
    "name": "string", 
    "address": "string",
    "gstin": "string"
  },
  "items": [
    {
      "description": "string",
      "quantity": number,
      "unit_price": number,
      "total_amount": number
    }
  ],
  "totals": {
    "subtotal": number,
    "cgst": number,
    "sgst": number,
    "igst": number,
    "grand_total": number
  },
  "currency": "string",
  "terms_conditions": "string"
}

CRITICAL RULES:
- Return ONLY valid JSON, no explanations
- Use ONLY actual values found in the OCR text - DO NOT make up or guess any data
- If a field is not found in the text, use empty string "" for text fields or 0 for numeric fields
- Do NOT use placeholder, mock, or example data
- If you cannot find the actual data, respond with "NO" for that field
- Extract GST numbers exactly as they appear in the text
- For dates, convert to YYYY-MM-DD format only if you can identify the actual date
- For amounts, use only the exact numbers found in the text"""

        human_prompt = f"Extract invoice data from this OCR text:\n\n{text}"
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            response = self.llm.invoke(messages)
            
            # Extract JSON from response
            response_text = response.content.strip()
            
            # Try to parse as JSON
            try:
                json_data = json.loads(response_text)
                print("✅ Successfully converted to JSON")
                return json_data
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                    print("✅ Successfully extracted and converted to JSON")
                    return json_data
                else:
                    print("❌ No valid JSON found in response")
                    return {"error": "No valid JSON in response", "raw_response": response_text}
                    
        except Exception as e:
            print(f"❌ Error calling Gemini API: {e}")
            return {"error": str(e)}
    
    def process_pdf(self, pdf_path: str, output_path: str = None) -> dict:
        """Complete workflow: PDF → OCR → JSON"""
        print("🚀 Starting PDF to JSON conversion")
        print("=" * 50)
        
        # Step 1: Extract text using OCR
        ocr_text = self.extract_text_from_pdf(pdf_path)
        
        # Step 2: Convert to JSON using Gemini
        json_data = self.convert_to_json(ocr_text)
        
        # Step 3: Save results
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = f"invoice_{filename}_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 JSON saved to: {output_path}")
        print("=" * 50)
        print("✅ Conversion completed successfully!")
        
        return json_data

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 2:
        print("Usage: python pdf_to_json.py <path_to_pdf>")
        print("Example: python pdf_to_json.py invoice.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        converter = PDFToJSON()
        result = converter.process_pdf(pdf_path)
        
        # Print summary
        print("\n📊 Extraction Summary:")
        print("-" * 30)
        if "invoice_number" in result:
            print(f"Invoice: {result.get('invoice_number', 'N/A')}")
        if "vendor" in result and "name" in result["vendor"]:
            print(f"Vendor: {result['vendor'].get('name', 'N/A')}")
        if "totals" in result and "grand_total" in result["totals"]:
            print(f"Total: ₹{result['totals'].get('grand_total', 0):,.2f}")
        if "items" in result:
            print(f"Items: {len(result['items'])} items")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()