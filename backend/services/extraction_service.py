from pathlib import Path
from typing import Any
from fastapi import HTTPException

from backend.core.config import settings
from backend.clients.modal_client import forward_request

def run_single_infer(label: str, extraction_schema: dict, pdf_path_str: str) -> Any:
    if not settings.REMOTE_ENABLED:
        raise HTTPException(status_code=503, detail="Remote inference not configured.")

    p = Path(pdf_path_str)
    if not p.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {pdf_path_str}")

    try:
        from backend.parsing.pdf_text_parser import PDFExtractor
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parser import error: {e}")

    pdf_content, _ = PDFExtractor.extract_pdf_text(pdf_path=str(p))

    payload = [{
        "label": label,
        "extraction_schema": extraction_schema,
        "pdf_path": str(p),
        "pdf_content": pdf_content,
    }]
    return forward_request(settings.MODAL_EXTRACTION_URL, data=payload, method="POST")
