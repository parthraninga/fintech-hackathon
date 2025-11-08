"""
Invoice Processing Service
Handles background processing of uploaded invoices including OCR extraction
"""

import os
import json
import subprocess
import asyncio
import time
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session
from models.invoice import Invoice, InvoiceStatus, AgentStage
from database import get_db
from utils.helpers import get_file_path

# Import WebSocket manager for real-time updates
import sys
sys.path.append('/Users/admin/gst-extractor/backend')
from routers.websockets import manager, broadcast_batch_update


class InvoiceProcessingService:
    """Service for processing uploaded invoices with multiple OCR methods"""
    
    def __init__(self):
        self.textract_script = "/Users/admin/gst-extractor/textract_analyzer.py"
        self.tesseract_script = "/Users/admin/gst-extractor/tesseract_ocr.py"
        self.results_dir = "/Users/admin/gst-extractor/json-results"
        
        # Create results directory if it doesn't exist
        os.makedirs(self.results_dir, exist_ok=True)
    
    async def process_invoice(self, invoice_id: int, db: Session = None) -> Dict[str, Any]:
        """
        Process a single invoice with both OCR methods
        
        Args:
            invoice_id: ID of the invoice to process
            db: Database session
            
        Returns:
            Dictionary with processing results
        """
        if db is None:
            db = next(get_db())
        
        try:
            # Get invoice from database
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if not invoice:
                raise ValueError(f"Invoice {invoice_id} not found")
            
            # Update status to processing
            invoice.status = InvoiceStatus.PROCESSING
            invoice.current_stage = AgentStage.OCR_EXTRACTION
            db.commit()
            
            # Send WebSocket update: Processing started
            await self._send_processing_update(invoice_id, {
                "type": "processing_started",
                "invoice_id": invoice_id,
                "filename": invoice.filename,
                "status": "Processing started",
                "timestamp": datetime.now().isoformat()
            })
            
            # Also send batch update
            await self._send_batch_progress_update(invoice.batch_id, db)
            
            print(f"🚀 Starting processing for invoice {invoice_id}: {invoice.filename}")
            
            # Get the PDF file path
            pdf_path = invoice.file_path
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            results = {
                "invoice_id": invoice_id,
                "filename": invoice.filename,
                "started_at": datetime.now().isoformat(),
                "textract_result": None,
                "tesseract_result": None,
                "timing": {},
                "errors": []
            }
            
            # Run Textract OCR with timing
            print(f"📄 Running Textract analysis...")
            await self._send_processing_update(invoice_id, {
                "type": "textract_started",
                "invoice_id": invoice_id,
                "status": "Running AWS Textract analysis...",
                "timestamp": datetime.now().isoformat()
            })
            
            textract_start = time.time()
            textract_result = await self._run_textract(pdf_path, invoice.filename, invoice_id)
            textract_duration = time.time() - textract_start
            results["timing"]["textract_duration"] = round(textract_duration, 2)
            
            if textract_result:
                results["textract_result"] = textract_result
                print(f"✅ Textract completed in {textract_duration:.2f}s: {textract_result.get('output_file')}")
                await self._send_processing_update(invoice_id, {
                    "type": "textract_completed",
                    "invoice_id": invoice_id,
                    "status": f"Textract completed in {textract_duration:.2f}s",
                    "duration": textract_duration,
                    "output_file": textract_result.get('output_file'),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                results["errors"].append("Textract analysis failed")
                print(f"❌ Textract failed after {textract_duration:.2f}s")
                await self._send_processing_update(invoice_id, {
                    "type": "textract_failed",
                    "invoice_id": invoice_id,
                    "status": f"Textract failed after {textract_duration:.2f}s",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Run Tesseract OCR with timing
            print(f"🔍 Running Tesseract OCR...")
            await self._send_processing_update(invoice_id, {
                "type": "tesseract_started",
                "invoice_id": invoice_id,
                "status": "Running Tesseract OCR analysis...",
                "timestamp": datetime.now().isoformat()
            })
            
            tesseract_start = time.time()
            tesseract_result = await self._run_tesseract(pdf_path, invoice.filename, invoice_id)
            tesseract_duration = time.time() - tesseract_start
            results["timing"]["tesseract_duration"] = round(tesseract_duration, 2)
            
            if tesseract_result:
                results["tesseract_result"] = tesseract_result
                print(f"✅ Tesseract completed in {tesseract_duration:.2f}s: {tesseract_result.get('output_file')}")
                await self._send_processing_update(invoice_id, {
                    "type": "tesseract_completed",
                    "invoice_id": invoice_id,
                    "status": f"Tesseract completed in {tesseract_duration:.2f}s",
                    "duration": tesseract_duration,
                    "output_file": tesseract_result.get('output_file'),
                    "timestamp": datetime.now().isoformat()
                })
            else:
                results["errors"].append("Tesseract OCR failed")
                print(f"❌ Tesseract failed after {tesseract_duration:.2f}s")
                await self._send_processing_update(invoice_id, {
                    "type": "tesseract_failed",
                    "invoice_id": invoice_id,
                    "status": f"Tesseract failed after {tesseract_duration:.2f}s",
                    "timestamp": datetime.now().isoformat()
                })
            
            # Calculate total processing time
            results["completed_at"] = datetime.now().isoformat()
            start_time = datetime.fromisoformat(results["started_at"])
            end_time = datetime.fromisoformat(results["completed_at"])
            total_duration = (end_time - start_time).total_seconds()
            results["timing"]["total_duration"] = round(total_duration, 2)
            
            # Update invoice with results
            await self._update_invoice_with_results(invoice, results, db)
            
            # Save combined results
            results_file = self._save_processing_results(invoice_id, invoice.filename, results)
            print(f"💾 Results saved to: {results_file}")
            
            # Send final completion update
            await self._send_processing_update(invoice_id, {
                "type": "processing_completed",
                "invoice_id": invoice_id,
                "status": f"Processing completed in {total_duration:.2f}s",
                "total_duration": total_duration,
                "textract_duration": results["timing"].get("textract_duration", 0),
                "tesseract_duration": results["timing"].get("tesseract_duration", 0),
                "results_file": results_file,
                "errors": results.get("errors", []),
                "timestamp": datetime.now().isoformat()
            })
            
            # Send final batch progress update
            await self._send_batch_progress_update(invoice.batch_id, db)
            
            return results
            
        except Exception as e:
            print(f"❌ Processing failed for invoice {invoice_id}: {e}")
            
            # Send error update via WebSocket
            await self._send_processing_update(invoice_id, {
                "type": "processing_failed",
                "invoice_id": invoice_id,
                "status": f"Processing failed: {str(e)}",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            # Update invoice status to error
            if 'invoice' in locals():
                invoice.status = InvoiceStatus.ERROR
                invoice.current_stage = AgentStage.ERROR
                db.commit()
            
            return {
                "invoice_id": invoice_id,
                "error": str(e),
                "processed_at": datetime.now().isoformat()
            }
    
    async def _send_processing_update(self, invoice_id: int, update_data: Dict[str, Any]):
        """Send real-time processing updates via WebSocket"""
        try:
            # Send to dashboard metrics for OCR progress tracking
            message = {
                "event": "ocr_processing_update",
                "data": update_data
            }
            
            # Send to all dashboard connections
            if "dashboard" in manager.active_connections:
                for websocket in manager.active_connections["dashboard"]:
                    try:
                        await websocket.send_json(message)
                    except:
                        pass  # Connection might be closed
                        
            print(f"📡 WebSocket update sent: {update_data['type']} for invoice {invoice_id}")
        except Exception as e:
            print(f"⚠️ Failed to send WebSocket update: {e}")
    
    async def _send_batch_progress_update(self, batch_id: int, db: Session):
        """Send batch progress update via WebSocket"""
        try:
            # Get batch statistics from database
            from models.batch import Batch as BatchModel
            batch = db.query(BatchModel).filter(BatchModel.id == batch_id).first()
            if not batch:
                return
            
            # Count invoices by status
            from models.invoice import InvoiceStatus
            total_count = len(batch.invoices)
            completed_count = sum(1 for inv in batch.invoices if inv.status == InvoiceStatus.COMPLETED)
            error_count = sum(1 for inv in batch.invoices if inv.status == InvoiceStatus.ERROR)
            processing_count = sum(1 for inv in batch.invoices if inv.status == InvoiceStatus.PROCESSING)
            
            # Determine batch status
            if completed_count == total_count:
                batch_status = "completed"
            elif error_count == total_count:
                batch_status = "failed"
            elif processing_count > 0:
                batch_status = "processing"
            else:
                batch_status = "in_progress"
            
            # Send batch update
            batch_update = {
                "batchId": batch.batch_number,
                "status": batch_status,
                "totalCount": total_count,
                "completedCount": completed_count,
                "errorCount": error_count,
                "flaggedCount": 0,  # TODO: Add flagged logic if needed
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to WebSocket
            await broadcast_batch_update(batch_id, {
                "event": "batch_progress_update",
                "data": batch_update
            })
            
            print(f"📊 Batch progress update sent: {batch.batch_number} - {batch_status} ({completed_count}/{total_count})")
            
        except Exception as e:
            print(f"⚠️ Failed to send batch progress update: {e}")
    
    async def _run_textract(self, pdf_path: str, filename: str, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Run Textract analysis on PDF"""
        try:
            # Prepare output path
            safe_filename = filename.replace('.pdf', '').replace(' ', '_')
            
            # Run textract analyzer
            process = await asyncio.create_subprocess_exec(
                'python3', self.textract_script, pdf_path,
                cwd=os.path.dirname(self.textract_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"Textract error: {stderr.decode()}")
                return None
            
            # Find the generated JSON file
            output_dir = os.path.dirname(pdf_path)
            textract_files = [f for f in os.listdir(output_dir) if f.startswith(f'textract_analysis_{safe_filename}') and f.endswith('.json')]
            
            if not textract_files:
                print("No Textract output file found")
                return None
            
            # Get the most recent file
            textract_file = sorted(textract_files)[-1]
            textract_path = os.path.join(output_dir, textract_file)
            
            # Move to results directory
            results_path = os.path.join(self.results_dir, textract_file)
            os.rename(textract_path, results_path)
            
            # Load and return results
            with open(results_path, 'r', encoding='utf-8') as f:
                textract_data = json.load(f)
            
            return {
                "output_file": results_path,
                "data": textract_data,
                "success": True
            }
            
        except Exception as e:
            print(f"Textract processing error: {e}")
            return None
    
    async def _run_tesseract(self, pdf_path: str, filename: str, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Run Tesseract OCR on PDF"""
        try:
            # Prepare output path
            safe_filename = filename.replace('.pdf', '').replace(' ', '_')
            output_base = os.path.join(self.results_dir, f"{safe_filename}_tesseract_ocr")
            
            # Run tesseract OCR
            process = await asyncio.create_subprocess_exec(
                'python3', self.tesseract_script, pdf_path,
                '--output', output_base,
                cwd=os.path.dirname(self.tesseract_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"Tesseract error: {stderr.decode()}")
                return None
            
            # Check for output files
            json_file = f"{output_base}.json"
            txt_file = f"{output_base}.txt"
            
            if not os.path.exists(json_file):
                print("No Tesseract JSON output file found")
                return None
            
            # Load and return results
            with open(json_file, 'r', encoding='utf-8') as f:
                tesseract_data = json.load(f)
            
            return {
                "output_file": json_file,
                "text_file": txt_file,
                "data": tesseract_data,
                "success": True
            }
            
        except Exception as e:
            print(f"Tesseract processing error: {e}")
            return None
    
    async def _update_invoice_with_results(self, invoice: Invoice, results: Dict[str, Any], db: Session):
        """Update invoice record with OCR results"""
        try:
            # Extract text from both methods for storage
            ocr_text = ""
            
            # Get Textract text
            if results.get("textract_result") and results["textract_result"].get("data"):
                textract_data = results["textract_result"]["data"]
                if "form_analysis" in textract_data:
                    form_fields = textract_data["form_analysis"].get("form_fields", [])
                    ocr_text += "TEXTRACT FORM FIELDS:\n"
                    for field in form_fields:
                        ocr_text += f"{field.get('key', '')}: {field.get('value', '')}\n"
            
            # Get Tesseract text
            if results.get("tesseract_result") and results["tesseract_result"].get("data"):
                tesseract_data = results["tesseract_result"]["data"]
                tesseract_text = tesseract_data.get("ocr_text", "")
                if tesseract_text:
                    ocr_text += "\n\nTESSERACT OCR TEXT:\n" + tesseract_text
            
            # Update invoice fields
            invoice.ocr_text = ocr_text
            invoice.status = InvoiceStatus.EXTRACTED if not results.get("errors") else InvoiceStatus.ERROR
            invoice.current_stage = AgentStage.DATA_EXTRACTION if not results.get("errors") else AgentStage.ERROR
            invoice.progress_percentage = 25.0  # OCR complete = 25%
            
            # Store processing results in extracted_data field
            invoice.extracted_data = json.dumps({
                "textract_file": results.get("textract_result", {}).get("output_file"),
                "tesseract_file": results.get("tesseract_result", {}).get("output_file"),
                "processing_errors": results.get("errors", []),
                "processed_at": results.get("processed_at")
            })
            
            db.commit()
            
        except Exception as e:
            print(f"Error updating invoice: {e}")
            invoice.status = InvoiceStatus.ERROR
            invoice.current_stage = AgentStage.ERROR
            db.commit()
    
    def _save_processing_results(self, invoice_id: int, filename: str, results: Dict[str, Any]) -> str:
        """Save combined processing results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace('.pdf', '').replace(' ', '_')
        results_file = os.path.join(self.results_dir, f"invoice_{invoice_id}_{safe_filename}_combined_{timestamp}.json")
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        return results_file


# Global service instance
processing_service = InvoiceProcessingService()


async def process_invoice_async(invoice_id: int):
    """Async function to process invoice (can be called from background task)"""
    db = next(get_db())
    try:
        return await processing_service.process_invoice(invoice_id, db)
    finally:
        db.close()