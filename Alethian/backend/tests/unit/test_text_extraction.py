import pytest
from unittest import mock
from app.core.text_extraction import extract_text_from_pdf

def test_text_extraction_fallback_to_ocr():
    # We will mock the three extraction functions directly to simulate fallback logic
    # instead of mocking the massive underlying C-libs like tesseract.
    with mock.patch("app.core.text_extraction.extract_with_grobid") as mock_grobid, \
         mock.patch("app.core.text_extraction.extract_with_pypdf") as mock_pypdf, \
         mock.patch("app.core.text_extraction.extract_with_ocr") as mock_ocr, \
         mock.patch("builtins.open", mock.mock_open(read_data=b"dummy bytes")):
            
            # 1. Simulate Grobid failing entirely
            mock_grobid.return_value = None
            
            # 2. Simulate pyPDF failing (e.g. image only PDF returning < MIN_TEXT_LENGTH)
            mock_pypdf.return_value = None
            
            # 3. Simulate Tesseract succeeding
            mock_ocr.return_value = "This is the magically recovered OCR text."
            
            # Build mock paths
            result = extract_text_from_pdf("dummy.pdf", b"dummy")
            
            assert mock_grobid.call_count == 1
            assert mock_pypdf.call_count == 1
            assert mock_ocr.call_count == 1
            
            # Since grobid failed, it returns a dict with "body_text" mapped to the OCR result
            assert result is not None
            assert result["body_text"] == "This is the magically recovered OCR text."
            assert result["title"] == "Unknown Title (OCR)"
