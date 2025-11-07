#!/usr/bin/env python3
"""
Simple Tesseract OCR for PDFs

Usage:
  python3 tesseract_ocr.py <path_to_pdf> [--output base_output_name] [--lang eng]

This script:
- Converts PDF pages to images using pdf2image
- Runs pytesseract OCR on each page
- Writes a plain text file and a JSON file containing the concatenated OCR text and metadata

Output files (by default for input `invoice.pdf`):
- invoice_ocr.txt
- invoice_ocr.json

If OCR cannot run (missing tesseract/poppler), the script prints "no" and exits with code 1.

"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from pdf2image import convert_from_path
    import pytesseract
except Exception as e:
    # We'll handle missing runtime deps later with friendly message
    pass


def check_dependencies():
    """Return (ok, message). If ok True, else False and message explains why."""
    # Check tesseract
    try:
        import pytesseract
        # try to get tesseract cmd
        tcmd = getattr(pytesseract, 'pytesseract', None)
    except Exception as e:
        return False, f"pytesseract not available: {e}"

    # Check pdf2image
    try:
        from pdf2image import convert_from_path  # noqa: F401
    except Exception as e:
        return False, f"pdf2image not available: {e}"

    # Poppler availability is required by pdf2image; convert_from_path will indicate if missing at runtime
    return True, "ok"


def ocr_pdf(pdf_path: Path, lang: str = 'eng', dpi: int = 300):
    """Convert pdf to images and run OCR. Returns full_text string."""
    try:
        images = convert_from_path(str(pdf_path), dpi=dpi)
    except Exception as e:
        raise RuntimeError(f"pdf->image conversion failed: {e}")

    page_texts = []
    for i, img in enumerate(images, start=1):
        try:
            text = pytesseract.image_to_string(img, lang=lang)
        except Exception as e:
            raise RuntimeError(f"pytesseract OCR failed on page {i}: {e}")
        page_texts.append(text)

    full_text = "\n\n---PAGE_BREAK---\n\n".join(page_texts)
    return full_text


def write_outputs(base_output: Path, filename: str, ocr_text: str, extra_meta: dict = None):
    txt_path = base_output.with_suffix('.txt')
    json_path = base_output.with_suffix('.json')

    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(ocr_text)

    payload = {
        'filename': filename,
        'ocr_text': ocr_text,
        'generated_at': __import__('datetime').datetime.now().isoformat()
    }
    if extra_meta:
        payload.update(extra_meta)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return txt_path, json_path


def main():
    parser = argparse.ArgumentParser(description='Convert PDF -> OCR text using Tesseract')
    parser.add_argument('pdf', help='Path to PDF file')
    parser.add_argument('--output', '-o', help='Base output filename (without extension)', default=None)
    parser.add_argument('--lang', '-l', help='Tesseract language code (default: eng)', default='eng')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for PDF to image conversion')

    args = parser.parse_args()
    pdf_path = Path(args.pdf)

    if not pdf_path.exists():
        print(f"no")
        print(f"Error: PDF file not found: {pdf_path}")
        sys.exit(1)

    ok, msg = check_dependencies()
    if not ok:
        # Per request: say no if it is not giving
        print('no')
        print(msg)
        sys.exit(1)

    # Determine output base
    if args.output:
        base_output = Path(args.output)
    else:
        stem = pdf_path.stem
        base_output = pdf_path.parent / f"{stem}_ocr"

    try:
        ocr_text = ocr_pdf(pdf_path, lang=args.lang, dpi=args.dpi)
    except Exception as e:
        print('no')
        print(f"OCR processing failed: {e}")
        sys.exit(1)

    # write outputs
    txt_path, json_path = write_outputs(base_output, pdf_path.name, ocr_text)

    print(f"OCR text written to: {txt_path}")
    print(f"OCR JSON written to: {json_path}")
    # Print json path on stdout for programmatic consumption
    print(str(json_path))


if __name__ == '__main__':
    main()
