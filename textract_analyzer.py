#!/usr/bin/env python3
"""
Amazon Textract PDF Analyzer

This script uses Amazon Textract to extract comprehensive details from PDFs:
- Raw text extraction
- Form field detection (key-value pairs)
- Table detection and extraction
- Layout analysis
- Handwriting detection
- Structured data output
"""

import boto3
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

class TextractPDFAnalyzer:
    def __init__(self):
        """Initialize Textract analyzer with AWS credentials"""
        self.aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        
        if not self.aws_access_key or not self.aws_secret_key:
            print("⚠️  AWS credentials not found in .env file")
            print("Please add:")
            print("AWS_ACCESS_KEY_ID=your_access_key")
            print("AWS_SECRET_ACCESS_KEY=your_secret_key")
            print("AWS_REGION=us-east-1  # optional, defaults to us-east-1")
            sys.exit(1)
        
        # Initialize Textract client
        try:
            self.textract = boto3.client(
                'textract',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )
            print(f"✅ AWS Textract initialized successfully (Region: {self.aws_region})")
        except Exception as e:
            print(f"❌ Failed to initialize AWS Textract: {e}")
            sys.exit(1)
    
    def analyze_document(self, pdf_path: str) -> Dict[str, Any]:
        """
        Comprehensive document analysis using Textract
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing all extracted information
        """
        print(f"📄 Starting comprehensive analysis of: {pdf_path}")
        print("=" * 60)
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Read PDF file
        with open(pdf_path, 'rb') as file:
            pdf_bytes = file.read()
        
        results = {
            "file_info": {
                "filename": os.path.basename(pdf_path),
                "file_size_bytes": len(pdf_bytes),
                "analyzed_at": datetime.now().isoformat()
            },
            "form_analysis": {},
            "table_analysis": {},
            "layout_analysis": {},
            "summary": {}
        }
        
        # 2. Form Analysis (key-value pairs)
        print("📝 Step 2: Form Field Analysis...")
        results["form_analysis"] = self._analyze_forms(pdf_bytes)
        
        # 3. Table Analysis
        print("📊 Step 3: Table Analysis...")
        results["table_analysis"] = self._analyze_tables(pdf_bytes)
        
        # 4. Layout Analysis (comprehensive)
        print("📋 Step 4: Layout Analysis...")
        results["layout_analysis"] = self._analyze_layout(pdf_bytes)
        
        # 5. Generate Summary
        print("📊 Step 5: Generating Summary...")
        results["summary"] = self._generate_summary(results)
        
        print("✅ Analysis completed successfully!")
        return results
    
    def _detect_text(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Basic text detection"""
        try:
            response = self.textract.detect_document_text(
                Document={'Bytes': pdf_bytes}
            )
            
            # Extract all text
            text_blocks = []
            confidence_scores = []
            
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text_blocks.append({
                        'text': block.get('Text', ''),
                        'confidence': block.get('Confidence', 0),
                        'bbox': block.get('Geometry', {}).get('BoundingBox', {})
                    })
                    confidence_scores.append(block.get('Confidence', 0))
            
            # Combine all text
            full_text = '\n'.join([block['text'] for block in text_blocks])
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
            
            return {
                'full_text': full_text,
                'text_blocks': text_blocks,
                'total_blocks': len(text_blocks),
                'average_confidence': round(avg_confidence, 2),
                'word_count': len(full_text.split()) if full_text else 0
            }
            
        except Exception as e:
            print(f"❌ Text detection failed: {e}")
            return {'error': str(e)}
    
    def _analyze_forms(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Analyze forms and extract key-value pairs"""
        try:
            response = self.textract.analyze_document(
                Document={'Bytes': pdf_bytes},
                FeatureTypes=['FORMS']
            )
            
            # Extract key-value pairs
            key_map = {}
            value_map = {}
            block_map = {}
            
            for block in response['Blocks']:
                block_id = block['Id']
                block_map[block_id] = block
                
                if block['BlockType'] == "KEY_VALUE_SET":
                    if 'KEY' in block['EntityTypes']:
                        key_map[block_id] = block
                    else:
                        value_map[block_id] = block
            
            # Build form fields
            form_fields = []
            for key_block_id, key_block in key_map.items():
                key_text = self._get_text_from_block(key_block, block_map)
                value_text = ""
                
                if 'Relationships' in key_block:
                    for relationship in key_block['Relationships']:
                        if relationship['Type'] == 'VALUE':
                            for value_id in relationship['Ids']:
                                if value_id in value_map:
                                    value_text = self._get_text_from_block(value_map[value_id], block_map)
                
                if key_text:
                    form_fields.append({
                        'key': key_text.strip(),
                        'value': value_text.strip(),
                        'confidence': key_block.get('Confidence', 0)
                    })
            
            return {
                'form_fields': form_fields,
                'total_fields': len(form_fields),
                'fields_with_values': len([f for f in form_fields if f['value']])
            }
            
        except Exception as e:
            print(f"❌ Form analysis failed: {e}")
            return {'error': str(e)}
    
    def _analyze_tables(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Analyze and extract tables"""
        try:
            response = self.textract.analyze_document(
                Document={'Bytes': pdf_bytes},
                FeatureTypes=['TABLES']
            )
            
            tables = []
            block_map = {block['Id']: block for block in response['Blocks']}
            
            for block in response['Blocks']:
                if block['BlockType'] == 'TABLE':
                    table = self._extract_table_data(block, block_map)
                    tables.append(table)
            
            return {
                'tables': tables,
                'total_tables': len(tables),
                'total_cells': sum(len(table['rows']) * len(table['rows'][0]) if table['rows'] else 0 for table in tables)
            }
            
        except Exception as e:
            print(f"❌ Table analysis failed: {e}")
            return {'error': str(e)}
    
    def _analyze_layout(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Comprehensive layout analysis"""
        try:
            response = self.textract.analyze_document(
                Document={'Bytes': pdf_bytes},
                FeatureTypes=['LAYOUT']
            )
            
            layout_elements = []
            for block in response['Blocks']:
                if block['BlockType'] == 'LAYOUT':
                    layout_elements.append({
                        'type': block.get('BlockType'),
                        'layout_type': block.get('LayoutType'),
                        'confidence': block.get('Confidence', 0),
                        'text': block.get('Text', ''),
                        'bbox': block.get('Geometry', {}).get('BoundingBox', {})
                    })
            
            return {
                'layout_elements': layout_elements,
                'total_elements': len(layout_elements),
                'element_types': list(set([elem['layout_type'] for elem in layout_elements if elem.get('layout_type')]))
            }
            
        except Exception as e:
            print(f"⚠️  Layout analysis not available: {e}")
            return {'message': 'Layout analysis requires advanced Textract features'}
    
    def _extract_table_data(self, table_block: Dict, block_map: Dict) -> Dict[str, Any]:
        """Extract structured data from a table"""
        rows = []
        current_row = []
        
        if 'Relationships' in table_block:
            for relationship in table_block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        cell_block = block_map.get(child_id)
                        if cell_block and cell_block['BlockType'] == 'CELL':
                            cell_text = self._get_text_from_block(cell_block, block_map)
                            row_index = cell_block.get('RowIndex', 1) - 1
                            col_index = cell_block.get('ColumnIndex', 1) - 1
                            
                            # Ensure we have enough rows
                            while len(rows) <= row_index:
                                rows.append([])
                            
                            # Ensure we have enough columns in this row
                            while len(rows[row_index]) <= col_index:
                                rows[row_index].append('')
                            
                            rows[row_index][col_index] = cell_text
        
        return {
            'rows': rows,
            'row_count': len(rows),
            'column_count': max(len(row) for row in rows) if rows else 0,
            'confidence': table_block.get('Confidence', 0)
        }
    
    def _get_text_from_block(self, block: Dict, block_map: Dict) -> str:
        """Extract text content from a block"""
        text = ""
        if 'Relationships' in block:
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    for child_id in relationship['Ids']:
                        child_block = block_map.get(child_id)
                        if child_block and child_block['BlockType'] == 'WORD':
                            text += child_block.get('Text', '') + ' '
        return text.strip()
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate analysis summary"""
        summary = {
            'document_type': 'Unknown',
            'confidence_score': 0,
            'key_findings': [],
            'recommended_actions': []
        }
        
        # Document type detection based on form fields
        form_fields = results.get('form_analysis', {}).get('form_fields', [])
        form_keys = [field['key'].lower() for field in form_fields]
        form_text = ' '.join(form_keys)
        
        if 'invoice' in form_text or 'bill' in form_text:
            summary['document_type'] = 'Invoice/Bill'
        elif 'receipt' in form_text:
            summary['document_type'] = 'Receipt'
        elif 'contract' in form_text or 'agreement' in form_text:
            summary['document_type'] = 'Contract/Agreement'
        elif 'form' in form_text or 'application' in form_text:
            summary['document_type'] = 'Form/Application'
        
        # Calculate overall confidence from forms only
        confidences = []
        if results.get('form_analysis', {}).get('form_fields'):
            field_confidences = [f['confidence'] for f in results['form_analysis']['form_fields']]
            if field_confidences:
                confidences.append(sum(field_confidences) / len(field_confidences))
        
        summary['confidence_score'] = round(sum(confidences) / len(confidences), 2) if confidences else 0
        
        # Key findings
        if results.get('form_analysis', {}).get('total_fields', 0) > 0:
            summary['key_findings'].append(f"Found {results['form_analysis']['total_fields']} form fields")
        
        if results.get('table_analysis', {}).get('total_tables', 0) > 0:
            summary['key_findings'].append(f"Found {results['table_analysis']['total_tables']} tables")
        
        return summary
    
    def save_results(self, results: Dict[str, Any], output_path: str = None) -> str:
        """Save analysis results to JSON file"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = results['file_info']['filename'].replace('.pdf', '')
            output_path = f"textract_analysis_{filename}_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Analysis results saved to: {output_path}")
        return output_path
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a formatted summary of the analysis"""
        print("\n" + "="*60)
        print("📊 TEXTRACT ANALYSIS SUMMARY")
        print("="*60)
        
        # File info
        file_info = results.get('file_info', {})
        print(f"📄 File: {file_info.get('filename', 'Unknown')}")
        print(f"📏 Size: {file_info.get('file_size_bytes', 0):,} bytes")
        
        # Summary
        summary = results.get('summary', {})
        print(f"📋 Type: {summary.get('document_type', 'Unknown')}")
        print(f"🎯 Confidence: {summary.get('confidence_score', 0)}%")
        
        # Forms
        forms = results.get('form_analysis', {})
        print(f"📝 Form fields: {forms.get('total_fields', 0)}")
        print(f"✅ Fields with values: {forms.get('fields_with_values', 0)}")
        
        # Tables
        tables = results.get('table_analysis', {})
        print(f"📊 Tables found: {tables.get('total_tables', 0)}")
        print(f"🔢 Total cells: {tables.get('total_cells', 0)}")
        
        # Key findings
        key_findings = summary.get('key_findings', [])
        if key_findings:
            print("\n🔍 Key Findings:")
            for finding in key_findings:
                print(f"  • {finding}")
        
        print("="*60)

def main():
    """Main function for command line usage"""
    if len(sys.argv) != 2:
        print("Usage: python textract_analyzer.py <path_to_pdf>")
        print("Example: python textract_analyzer.py invoice.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    try:
        # Initialize analyzer
        analyzer = TextractPDFAnalyzer()
        
        # Analyze document
        results = analyzer.analyze_document(pdf_path)
        
        # Save results
        output_file = analyzer.save_results(results)
        
        # Print summary
        analyzer.print_summary(results)
        
        print(f"\n💡 Full results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()