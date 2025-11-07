import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException

from backend.core.config import settings
from backend.core.responses import pretty_response
from backend.schemas.v1.schemas import BatchRequest
from backend.services.extraction_service import run_single_infer
from backend.services.dataset_utils import resolve_pdf_path_from_sample, materialize_filled_item

router = APIRouter()

@router.post("/batch")
def batch(request: BatchRequest):
    if not settings.REMOTE_ENABLED:
        raise HTTPException(status_code=503, detail="Remote batch not configured.")
    root = Path(request.pdfs_root_path).expanduser().resolve()
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid PDF root folder: {root}")
    ds_path = Path(request.json_path).expanduser().resolve()
    if not ds_path.is_file():
        raise HTTPException(status_code=404, detail=f"Dataset not found: {ds_path}")
    try:
        dataset: List[dict] = json.loads(ds_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid dataset JSON: {e}")

    filled_array: List[dict] = []
    for sample in dataset:
        try:
            pdf_path, _ = resolve_pdf_path_from_sample(sample, root)
        except ValueError:
            empty = {k: None for k in (sample.get("extraction_schema") or {}).keys()}
            filled_array.append({
                "label": sample.get("label"),
                "extraction_schema": empty,
                **({"pdf_path": sample.get("pdf_path")} if "pdf_path" in sample else {}),
                **({"pdf_filename": sample.get("pdf_filename")} if "pdf_filename" in sample else {}),
                "_error": "bad reference",
            })
            continue

        if not pdf_path.is_file():
            empty = {k: None for k in (sample.get("extraction_schema") or {}).keys()}
            filled_array.append({
                "label": sample.get("label"),
                "extraction_schema": empty,
                **({"pdf_path": sample.get("pdf_path")} if "pdf_path" in sample else {}),
                **({"pdf_filename": sample.get("pdf_filename")} if "pdf_filename" in sample else {}),
                "_error": f"File not found: {pdf_path}",
            })
            continue

        try:
            modal_res = run_single_infer(sample.get("label"), sample.get("extraction_schema"), str(pdf_path))
            modal_item = (modal_res or [{}])[0]
            filled_array.append(materialize_filled_item(sample, modal_item))
        except Exception as e:
            empty = {k: None for k in (sample.get("extraction_schema") or {}).keys()}
            filled_array.append({
                "label": sample.get("label"),
                "extraction_schema": empty,
                **({"pdf_path": sample.get("pdf_path")} if "pdf_path" in sample else {}),
                **({"pdf_filename": sample.get("pdf_filename")} if "pdf_filename" in sample else {}),
                "_error": str(e),
            })

    return pretty_response(filled_array)
