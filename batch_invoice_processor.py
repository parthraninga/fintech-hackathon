#!/usr/bin/env python3
"""
Batch Invoice Processor with Dual-Input AI Agent

This script processes multiple invoice documents in batch mode by:
1. Scanning a folder for pairs of files: doc_id_ocr.json and textract_analysis_doc_id
2. Processing each pair using the same dual-input AI logic
3. Generating comprehensive reports for each document
4. Providing batch summary statistics and insights

Features:
- Batch processing of multiple invoice documents
- Automatic file pairing and validation
- Progress tracking and error handling
- Batch statistics and summary reports
- Individual PDF reports for each processed document
- Consolidated batch summary with insights
- Memory-efficient processing for large batches
"""

import json
import os
import sys
import glob
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import time
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
from dataclasses import dataclass

# Import the existing dual input agent
from dual_input_ai_agent import DualInputInvoiceAI, AgentState, ExtractedInvoiceData
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class BatchProcessingResult:
    """Result of processing a single document in batch"""
    doc_id: str
    textract_file: str
    ocr_file: str
    success: bool
    processing_time: float
    extracted_data: Optional[ExtractedInvoiceData] = None
    database_ids: Optional[Dict[str, int]] = None
    validation_result: Optional[Dict[str, Any]] = None
    duplication_analysis: Optional[Dict[str, Any]] = None
    ai_reasoning: Optional[Dict[str, Any]] = None
    pdf_report_path: Optional[str] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

@dataclass
class BatchSummary:
    """Summary statistics for batch processing"""
    total_documents: int
    successful_processed: int
    failed_processed: int
    total_processing_time: float
    average_processing_time: float
    
    # Financial summaries
    total_invoice_amount: float = 0.0
    total_tax_amount: float = 0.0
    unique_suppliers: int = 0
    
    # Validation statistics
    validation_passed: int = 0
    validation_failed: int = 0
    
    # Duplication statistics
    duplicates_detected: int = 0
    unique_documents: int = 0
    
    # Document type breakdown
    document_types: Dict[str, int] = None
    
    # Top suppliers by volume
    top_suppliers: List[Dict[str, Any]] = None
    
    # Processing insights
    insights: List[str] = None
    
    def __post_init__(self):
        if self.document_types is None:
            self.document_types = {}
        if self.top_suppliers is None:
            self.top_suppliers = []
        if self.insights is None:
            self.insights = []

class BatchInvoiceProcessor:
    """Batch processor for multiple invoice documents"""
    
    def __init__(self, google_api_key: str = None, db_path: str = "invoice_management.db", max_workers: int = None):
        """Initialize batch processor"""
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        self.db_path = db_path
        self.max_workers = max_workers or min(4, multiprocessing.cpu_count())
        
        # Initialize a single agent for sequential processing (safer for database operations)
        self.agent = DualInputInvoiceAI(google_api_key=self.google_api_key, db_path=db_path)
        
        print(f"🚀 Batch Invoice Processor Initialized")
        print(f"   Database: {db_path}")
        print(f"   Max Workers: {self.max_workers}")
        print(f"   LLM: {'Google Gemini' if self.google_api_key else 'Rule-based processing'}")
    
    def find_document_pairs(self, folder_path: str) -> List[Tuple[str, str, str]]:
        """
        Find pairs of textract and OCR files in the folder
        Returns: List of (doc_id, textract_file_path, ocr_file_path)
        """
        folder_path = Path(folder_path)
        if not folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {folder_path}")
        
        print(f"🔍 Scanning folder: {folder_path}")
        
        # Find all OCR files with pattern: *_ocr.json
        ocr_files = glob.glob(str(folder_path / "*_ocr.json"))
        print(f"   Found {len(ocr_files)} OCR files")
        
        # Find all textract files with pattern: textract_analysis_*
        textract_files = glob.glob(str(folder_path / "textract_analysis_*"))
        print(f"   Found {len(textract_files)} Textract files")
        
        document_pairs = []
        
        for ocr_file in ocr_files:
            # Extract doc_id from OCR filename: doc_id_ocr.json -> doc_id
            ocr_basename = os.path.basename(ocr_file)
            doc_id_match = re.match(r'(.+)_ocr\.json$', ocr_basename)
            
            if not doc_id_match:
                print(f"   ⚠️ Skipping OCR file with invalid format: {ocr_basename}")
                continue
            
            doc_id = doc_id_match.group(1)
            
            # Look for corresponding textract file: textract_analysis_doc_id*
            matching_textract = [
                tf for tf in textract_files 
                if os.path.basename(tf).startswith(f"textract_analysis_{doc_id}")
            ]
            
            if matching_textract:
                textract_file = matching_textract[0]  # Use first match
                document_pairs.append((doc_id, textract_file, ocr_file))
                print(f"   ✅ Pair found: {doc_id}")
                print(f"      Textract: {os.path.basename(textract_file)}")
                print(f"      OCR: {os.path.basename(ocr_file)}")
            else:
                print(f"   ❌ No matching textract file for: {ocr_basename}")
        
        print(f"\n📊 Found {len(document_pairs)} valid document pairs to process")
        return document_pairs
    
    def process_single_document(self, doc_id: str, textract_file: str, ocr_file: str) -> BatchProcessingResult:
        """Process a single document pair"""
        print(f"\n{'='*60}")
        print(f"🔄 Processing Document: {doc_id}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Validate files exist
            if not os.path.exists(textract_file):
                raise FileNotFoundError(f"Textract file not found: {textract_file}")
            if not os.path.exists(ocr_file):
                raise FileNotFoundError(f"OCR file not found: {ocr_file}")
            
            # Process using dual input agent
            result = self.agent.process_dual_inputs(textract_file, ocr_file)
            
            processing_time = time.time() - start_time
            
            # Create batch result
            batch_result = BatchProcessingResult(
                doc_id=doc_id,
                textract_file=textract_file,
                ocr_file=ocr_file,
                success=result.get("success", False),
                processing_time=processing_time,
                extracted_data=result.get("extracted_data"),
                database_ids=result.get("database_ids"),
                validation_result=result.get("validation_result"),
                duplication_analysis=result.get("duplication_analysis"),
                ai_reasoning=result.get("ai_reasoning"),
                pdf_report_path=result.get("pdf_report_path"),
                errors=result.get("errors", [])
            )
            
            # Print processing summary
            status = "✅ SUCCESS" if batch_result.success else "❌ FAILED"
            print(f"\n{status} - Document {doc_id}")
            print(f"   Processing Time: {processing_time:.2f}s")
            
            if batch_result.extracted_data:
                extracted = batch_result.extracted_data
                print(f"   Invoice: {extracted.invoice_number}")
                print(f"   Supplier: {extracted.supplier_name}")
                print(f"   Amount: ₹{extracted.total_amount:,.2f}" if extracted.total_amount else "N/A")
            
            if batch_result.errors:
                print(f"   Errors: {len(batch_result.errors)}")
                for error in batch_result.errors[:2]:  # Show first 2 errors
                    print(f"     • {error}")
            
            return batch_result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Processing failed for {doc_id}: {str(e)}"
            print(f"❌ {error_msg}")
            
            return BatchProcessingResult(
                doc_id=doc_id,
                textract_file=textract_file,
                ocr_file=ocr_file,
                success=False,
                processing_time=processing_time,
                errors=[error_msg]
            )
    
    def process_batch(self, folder_path: str, parallel: bool = False) -> Tuple[List[BatchProcessingResult], BatchSummary]:
        """
        Process all document pairs in the folder
        
        Args:
            folder_path: Path to folder containing document files
            parallel: Whether to use parallel processing (experimental)
        
        Returns:
            Tuple of (results_list, batch_summary)
        """
        print(f"🚀 Starting Batch Processing")
        print(f"   Folder: {folder_path}")
        print(f"   Parallel: {parallel}")
        
        batch_start_time = time.time()
        
        # Find document pairs
        try:
            document_pairs = self.find_document_pairs(folder_path)
        except Exception as e:
            print(f"❌ Failed to scan folder: {e}")
            return [], BatchSummary(0, 0, 0, 0.0, 0.0)
        
        if not document_pairs:
            print("❌ No valid document pairs found in the folder")
            return [], BatchSummary(0, 0, 0, 0.0, 0.0)
        
        # Process documents
        results = []
        
        if parallel and len(document_pairs) > 1:
            # Parallel processing (experimental - may have database concurrency issues)
            print(f"⚡ Using parallel processing with {self.max_workers} workers")
            # Note: Parallel processing disabled for database safety
            print("⚠️  Parallel processing disabled for database safety. Using sequential processing.")
            parallel = False
        
        if not parallel:
            # Sequential processing (safer for database operations)
            print(f"🔄 Using sequential processing for {len(document_pairs)} documents")
            
            for i, (doc_id, textract_file, ocr_file) in enumerate(document_pairs, 1):
                print(f"\n📄 Processing {i}/{len(document_pairs)}: {doc_id}")
                
                result = self.process_single_document(doc_id, textract_file, ocr_file)
                results.append(result)
                
                # Progress update
                progress = (i / len(document_pairs)) * 100
                print(f"📊 Batch Progress: {progress:.1f}% ({i}/{len(document_pairs)})")
                
                # Small delay to prevent overwhelming the system
                time.sleep(0.5)
        
        batch_end_time = time.time()
        total_batch_time = batch_end_time - batch_start_time
        
        # Generate batch summary
        summary = self._generate_batch_summary(results, total_batch_time)
        
        # Print batch results
        self._print_batch_summary(results, summary)
        
        return results, summary
    
    def _generate_batch_summary(self, results: List[BatchProcessingResult], total_time: float) -> BatchSummary:
        """Generate comprehensive batch summary"""
        total_docs = len(results)
        successful = sum(1 for r in results if r.success)
        failed = total_docs - successful
        avg_time = total_time / total_docs if total_docs > 0 else 0.0
        
        # Financial summaries
        total_amount = 0.0
        total_tax = 0.0
        suppliers = set()
        document_types = {}
        
        # Validation and duplication stats
        validation_passed = 0
        validation_failed = 0
        duplicates_detected = 0
        unique_documents = 0
        
        supplier_amounts = {}
        
        for result in results:
            if result.success and result.extracted_data:
                extracted = result.extracted_data
                
                # Financial data
                if extracted.total_amount:
                    total_amount += extracted.total_amount
                if extracted.total_tax:
                    total_tax += extracted.total_tax
                
                # Supplier tracking
                if extracted.supplier_name:
                    suppliers.add(extracted.supplier_name)
                    supplier_amounts[extracted.supplier_name] = supplier_amounts.get(
                        extracted.supplier_name, 0.0
                    ) + (extracted.total_amount or 0.0)
                
                # Document types
                doc_type = extracted.document_type
                document_types[doc_type] = document_types.get(doc_type, 0) + 1
            
            # Validation stats
            if result.validation_result:
                if result.validation_result.get('overall_passed'):
                    validation_passed += 1
                else:
                    validation_failed += 1
            
            # Duplication stats
            if result.duplication_analysis:
                if result.duplication_analysis.get('is_duplicate'):
                    duplicates_detected += 1
                else:
                    unique_documents += 1
        
        # Top suppliers
        top_suppliers = [
            {"name": name, "total_amount": amount, "invoice_count": 1}
            for name, amount in sorted(supplier_amounts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Generate insights
        insights = []
        if successful > 0:
            insights.append(f"Successfully processed {successful}/{total_docs} documents ({successful/total_docs*100:.1f}%)")
            insights.append(f"Total invoice value: ₹{total_amount:,.2f}")
            insights.append(f"Average processing time: {avg_time:.2f}s per document")
            
            if validation_passed > 0:
                insights.append(f"Validation success rate: {validation_passed/(validation_passed+validation_failed)*100:.1f}%")
            
            if duplicates_detected > 0:
                insights.append(f"⚠️ {duplicates_detected} potential duplicates detected")
            
            if len(suppliers) > 0:
                insights.append(f"Processed invoices from {len(suppliers)} unique suppliers")
        
        return BatchSummary(
            total_documents=total_docs,
            successful_processed=successful,
            failed_processed=failed,
            total_processing_time=total_time,
            average_processing_time=avg_time,
            total_invoice_amount=total_amount,
            total_tax_amount=total_tax,
            unique_suppliers=len(suppliers),
            validation_passed=validation_passed,
            validation_failed=validation_failed,
            duplicates_detected=duplicates_detected,
            unique_documents=unique_documents,
            document_types=document_types,
            top_suppliers=top_suppliers,
            insights=insights
        )
    
    def _print_batch_summary(self, results: List[BatchProcessingResult], summary: BatchSummary):
        """Print comprehensive batch processing summary"""
        print(f"\n{'='*80}")
        print(f"📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*80}")
        
        # Processing Statistics
        print(f"📄 Document Processing:")
        print(f"   Total Documents: {summary.total_documents}")
        print(f"   ✅ Successful: {summary.successful_processed}")
        print(f"   ❌ Failed: {summary.failed_processed}")
        print(f"   📈 Success Rate: {summary.successful_processed/summary.total_documents*100:.1f}%")
        
        # Timing Statistics
        print(f"\n⏱️  Processing Performance:")
        print(f"   Total Time: {summary.total_processing_time:.2f}s")
        print(f"   Average Time: {summary.average_processing_time:.2f}s per document")
        print(f"   Throughput: {60/summary.average_processing_time:.1f} docs/minute" if summary.average_processing_time > 0 else "N/A")
        
        # Financial Summary
        if summary.total_invoice_amount > 0:
            print(f"\n💰 Financial Summary:")
            print(f"   Total Invoice Value: ₹{summary.total_invoice_amount:,.2f}")
            print(f"   Total Tax Amount: ₹{summary.total_tax_amount:,.2f}")
            print(f"   Average Invoice Value: ₹{summary.total_invoice_amount/summary.successful_processed:,.2f}")
            print(f"   Unique Suppliers: {summary.unique_suppliers}")
        
        # Validation Summary
        total_validated = summary.validation_passed + summary.validation_failed
        if total_validated > 0:
            print(f"\n✅ Validation Summary:")
            print(f"   Passed: {summary.validation_passed}/{total_validated}")
            print(f"   Failed: {summary.validation_failed}/{total_validated}")
            print(f"   Success Rate: {summary.validation_passed/total_validated*100:.1f}%")
        
        # Duplication Summary
        total_dup_analyzed = summary.duplicates_detected + summary.unique_documents
        if total_dup_analyzed > 0:
            print(f"\n🔍 Duplication Analysis:")
            print(f"   Unique Documents: {summary.unique_documents}")
            print(f"   Potential Duplicates: {summary.duplicates_detected}")
            if summary.duplicates_detected > 0:
                print(f"   ⚠️  Duplication Rate: {summary.duplicates_detected/total_dup_analyzed*100:.1f}%")
        
        # Document Types
        if summary.document_types:
            print(f"\n📋 Document Types:")
            for doc_type, count in summary.document_types.items():
                print(f"   {doc_type}: {count}")
        
        # Top Suppliers
        if summary.top_suppliers:
            print(f"\n🏢 Top Suppliers by Value:")
            for i, supplier in enumerate(summary.top_suppliers[:5], 1):
                print(f"   {i}. {supplier['name']}: ₹{supplier['total_amount']:,.2f}")
        
        # Key Insights
        if summary.insights:
            print(f"\n💡 Key Insights:")
            for insight in summary.insights:
                print(f"   • {insight}")
        
        # Failed Documents (if any)
        failed_results = [r for r in results if not r.success]
        if failed_results:
            print(f"\n❌ Failed Documents ({len(failed_results)}):")
            for result in failed_results:
                print(f"   • {result.doc_id}: {result.errors[0] if result.errors else 'Unknown error'}")
        
        print(f"{'='*80}")
        
        # Report generation summary
        pdf_reports = [r for r in results if r.pdf_report_path]
        if pdf_reports:
            print(f"📄 Generated {len(pdf_reports)} individual PDF reports")
        
        print(f"✅ Batch processing completed!")
    
    def save_batch_report(self, results: List[BatchProcessingResult], summary: BatchSummary, output_file: str = None):
        """Save batch processing report to JSON file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"batch_processing_report_{timestamp}.json"
        
        report_data = {
            "batch_summary": {
                "total_documents": summary.total_documents,
                "successful_processed": summary.successful_processed,
                "failed_processed": summary.failed_processed,
                "total_processing_time": summary.total_processing_time,
                "average_processing_time": summary.average_processing_time,
                "total_invoice_amount": summary.total_invoice_amount,
                "total_tax_amount": summary.total_tax_amount,
                "unique_suppliers": summary.unique_suppliers,
                "validation_passed": summary.validation_passed,
                "validation_failed": summary.validation_failed,
                "duplicates_detected": summary.duplicates_detected,
                "unique_documents": summary.unique_documents,
                "document_types": summary.document_types,
                "top_suppliers": summary.top_suppliers,
                "insights": summary.insights
            },
            "individual_results": [
                {
                    "doc_id": result.doc_id,
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "invoice_number": result.extracted_data.invoice_number if result.extracted_data else None,
                    "supplier_name": result.extracted_data.supplier_name if result.extracted_data else None,
                    "total_amount": result.extracted_data.total_amount if result.extracted_data else None,
                    "validation_passed": result.validation_result.get('overall_passed') if result.validation_result else None,
                    "is_duplicate": result.duplication_analysis.get('is_duplicate') if result.duplication_analysis else None,
                    "pdf_report_path": result.pdf_report_path,
                    "errors": result.errors
                }
                for result in results
            ],
            "timestamp": datetime.now().isoformat(),
            "processing_metadata": {
                "processor_version": "1.0.0",
                "database_path": self.db_path,
                "llm_enabled": bool(self.google_api_key)
            }
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"📊 Batch report saved: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Failed to save batch report: {e}")
            return None
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'agent') and self.agent:
            self.agent.db.close()
            print("🔒 Batch processor resources closed")

def main():
    """Main function for batch processing"""
    if len(sys.argv) < 2:
        print("Usage: python batch_invoice_processor.py <folder_path> [--parallel]")
        print("Example: python batch_invoice_processor.py /path/to/documents/")
        print("         python batch_invoice_processor.py ./invoice_docs/ --parallel")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    parallel = '--parallel' in sys.argv
    
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        sys.exit(1)
    
    # Initialize batch processor
    processor = BatchInvoiceProcessor()
    
    try:
        # Process batch
        results, summary = processor.process_batch(folder_path, parallel=parallel)
        
        # Save batch report
        report_file = processor.save_batch_report(results, summary)
        
        # Print final status
        if summary.successful_processed > 0:
            print(f"\n🎉 Batch processing completed!")
            print(f"   Processed: {summary.successful_processed}/{summary.total_documents} documents")
            print(f"   Total Value: ₹{summary.total_invoice_amount:,.2f}")
            if report_file:
                print(f"   Report: {report_file}")
        else:
            print(f"\n❌ Batch processing failed - no documents processed successfully")
            
    except KeyboardInterrupt:
        print(f"\n⚠️ Batch processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Batch processing failed: {e}")
    finally:
        processor.close()

if __name__ == "__main__":
    main()