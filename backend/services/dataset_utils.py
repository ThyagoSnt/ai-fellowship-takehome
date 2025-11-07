from pathlib import Path
from typing import Any, Dict, Tuple

def resolve_pdf_path_from_sample(sample: dict, root: Path) -> Tuple[Path, str]:
    ref = sample.get("pdf_path") or sample.get("pdf_filename")
    if not isinstance(ref, str) or not ref.strip():
        raise ValueError("Item missing 'pdf_path' or 'pdf_filename'")
    p = Path(ref)
    if not p.is_absolute():
        p = root / ref
    return p.resolve(), ref

def materialize_filled_item(sample: dict, modal_item: dict) -> dict:
    requested_fields: dict = (modal_item or {}).get("requested_fields") or {}
    input_schema: dict = sample.get("extraction_schema") or {}
    filled_schema: Dict[str, Any] = {k: requested_fields.get(k, None) for k in input_schema.keys()}
    filled = {"label": sample.get("label"), "extraction_schema": filled_schema}
    if "pdf_path" in sample:
        filled["pdf_path"] = sample["pdf_path"]
    elif "pdf_filename" in sample:
        filled["pdf_filename"] = sample["pdf_filename"]
    return filled
