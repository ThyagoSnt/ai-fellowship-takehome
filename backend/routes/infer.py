import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from backend.core.config import settings
from backend.core.responses import pretty_download
from backend.schemas.v1.schemas import InferenceRequest
from backend.services.extraction_service import run_single_infer
from backend.services.dataset_utils import materialize_filled_item

router = APIRouter()

@router.post("/infer")
def infer(request: InferenceRequest):
    if not settings.REMOTE_ENABLED:
        raise HTTPException(status_code=503, detail="Remote inference not configured.")
    file_path = Path(request.pdf_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {request.pdf_path}")
    t0 = time.perf_counter()
    modal_res = run_single_infer(request.label, request.extraction_schema, str(file_path))
    _duration_ms = int((time.perf_counter() - t0) * 1000)  # kept for parity
    modal_item = (modal_res or [{}])[0]
    sample_for_output = {"label": request.label, "extraction_schema": request.extraction_schema, "pdf_path": file_path.name}
    filled = materialize_filled_item(sample_for_output, modal_item)
    return filled

@router.post("/infer/download")
def infer_download(request: InferenceRequest):
    if not settings.REMOTE_ENABLED:
        raise HTTPException(status_code=503, detail="Remote inference not configured.")
    file_path = Path(request.pdf_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {request.pdf_path}")
    modal_res = run_single_infer(request.label, request.extraction_schema, str(file_path))
    modal_item = (modal_res or [{}])[0]
    sample_for_output = {"label": request.label, "extraction_schema": request.extraction_schema, "pdf_path": file_path.name}
    filled = materialize_filled_item(sample_for_output, modal_item)
    return pretty_download(filled, filename="single_result.json")
