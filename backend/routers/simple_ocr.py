"""
Simple OCR API endpoint for direct PDF processing
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import tempfile
import asyncio
import time
from datetime import datetime
from pathlib import Path

router = APIRouter()

@router.post("/simple-ocr")
async def simple_ocr_extraction(file: UploadFile = File(...)):
    """
    Simple OCR extraction endpoint - no authentication required
    Processes PDF with both Textract and Tesseract, returns JSON file paths
    """
    
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_pdf_path = temp_file.name
    
    try:
        start_time = time.time()
        
        # Prepare scripts paths
        textract_script = "/Users/admin/gst-extractor/textract_analyzer.py"
        tesseract_script = "/Users/admin/gst-extractor/tesseract_ocr.py"
        
        # Ensure scripts exist
        if not os.path.exists(textract_script):
            raise HTTPException(status_code=500, detail="Textract analyzer script not found")
        if not os.path.exists(tesseract_script):
            raise HTTPException(status_code=500, detail="Tesseract OCR script not found")
        
        results = {
            "filename": file.filename,
            "processing_started": datetime.now().isoformat(),
            "textract_file": None,
            "tesseract_file": None,
            "processing_time": None,
            "errors": []
        }
        
        # Run Textract analysis
        try:
            print(f"🔍 Running Textract analysis on {file.filename}...")
            textract_process = await asyncio.create_subprocess_exec(
                'python3', textract_script, temp_pdf_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            textract_stdout, textract_stderr = await textract_process.communicate()
            
            if textract_process.returncode == 0:
                # Find generated Textract JSON file
                temp_dir = os.path.dirname(temp_pdf_path)
                safe_filename = Path(file.filename).stem.replace(' ', '_')
                
                # Look for Textract output files
                textract_files = [f for f in os.listdir(temp_dir) 
                                if f.startswith(f'textract_analysis_{safe_filename}') and f.endswith('.json')]
                
                if textract_files:
                    textract_file = os.path.join(temp_dir, sorted(textract_files)[-1])
                    
                    # Move to results directory
                    results_dir = "/Users/admin/gst-extractor/json-results"
                    os.makedirs(results_dir, exist_ok=True)
                    
                    final_textract_path = os.path.join(results_dir, os.path.basename(textract_file))
                    os.rename(textract_file, final_textract_path)
                    results["textract_file"] = final_textract_path
                    print(f"✅ Textract completed: {final_textract_path}")
                else:
                    results["errors"].append("Textract: No output file generated")
            else:
                error_msg = textract_stderr.decode() if textract_stderr else "Unknown Textract error"
                results["errors"].append(f"Textract failed: {error_msg}")
                print(f"❌ Textract failed: {error_msg}")
        
        except Exception as e:
            results["errors"].append(f"Textract exception: {str(e)}")
            print(f"❌ Textract exception: {e}")
        
        # Run Tesseract OCR
        try:
            print(f"🔍 Running Tesseract OCR on {file.filename}...")
            
            # Generate output base name
            temp_dir = os.path.dirname(temp_pdf_path)
            safe_filename = Path(file.filename).stem.replace(' ', '_')
            output_base = os.path.join(temp_dir, f"{safe_filename}_tesseract_ocr")
            
            tesseract_process = await asyncio.create_subprocess_exec(
                'python3', tesseract_script, temp_pdf_path,
                '--output', output_base,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            tesseract_stdout, tesseract_stderr = await tesseract_process.communicate()
            
            if tesseract_process.returncode == 0:
                tesseract_json = f"{output_base}.json"
                tesseract_txt = f"{output_base}.txt"
                
                if os.path.exists(tesseract_json):
                    # Move to results directory
                    results_dir = "/Users/admin/gst-extractor/json-results"
                    os.makedirs(results_dir, exist_ok=True)
                    
                    final_tesseract_json = os.path.join(results_dir, os.path.basename(tesseract_json))
                    final_tesseract_txt = os.path.join(results_dir, os.path.basename(tesseract_txt))
                    
                    os.rename(tesseract_json, final_tesseract_json)
                    if os.path.exists(tesseract_txt):
                        os.rename(tesseract_txt, final_tesseract_txt)
                    
                    results["tesseract_file"] = final_tesseract_json
                    print(f"✅ Tesseract completed: {final_tesseract_json}")
                else:
                    results["errors"].append("Tesseract: No JSON output file generated")
            else:
                error_msg = tesseract_stderr.decode() if tesseract_stderr else "Unknown Tesseract error"
                results["errors"].append(f"Tesseract failed: {error_msg}")
                print(f"❌ Tesseract failed: {error_msg}")
        
        except Exception as e:
            results["errors"].append(f"Tesseract exception: {str(e)}")
            print(f"❌ Tesseract exception: {e}")
        
        # Calculate processing time
        end_time = time.time()
        results["processing_time"] = round(end_time - start_time, 2)
        results["processing_completed"] = datetime.now().isoformat()
        
        print(f"🎉 OCR processing completed in {results['processing_time']}s")
        
        # Return results
        if results["textract_file"] or results["tesseract_file"]:
            return JSONResponse(content=results)
        else:
            # Both methods failed
            raise HTTPException(
                status_code=500, 
                detail={
                    "message": "Both OCR methods failed",
                    "errors": results["errors"]
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_pdf_path)
        except:
            pass
