import time
import asyncio
from pathlib import Path
from typing import List
from fastapi import HTTPException

from backend.core.sse import sse_format
from backend.models.job_model import BatchJob
from backend.services.dataset_utils import resolve_pdf_path_from_sample, materialize_filled_item
from backend.services.extraction_service import run_single_infer

async def run_batch_job(job: BatchJob, dataset: List[dict], root: Path) -> None:
    await job.queue.put({"type": "start", "job_id": job.id, "total": job.total, "processed": 0, "status": job.status})
    loop = asyncio.get_running_loop()

    for i, sample in enumerate(dataset):
        try:
            pdf_path, ref = resolve_pdf_path_from_sample(sample, root)
        except ValueError as e:
            empty = {k: None for k in (sample.get("extraction_schema") or {}).keys()}
            filled = {"label": sample.get("label"), "extraction_schema": empty}
            if "pdf_path" in sample: filled["pdf_path"] = sample["pdf_path"]
            if "pdf_filename" in sample: filled["pdf_filename"] = sample["pdf_filename"]
            file_name = (sample.get("pdf_path") or sample.get("pdf_filename") or f"item_{i}.pdf").split("/")[-1]
            job.filled_items.append(filled)
            job.meta_items.append({"index": i, "file_name": file_name, "status": "error", "response_ms": 0, "error": str(e)})
            job.processed += 1
            await job.queue.put({
                "type": "item_error",
                "job_id": job.id,
                "index": i,
                "file_name": file_name,
                "response_ms": 0,
                "error": str(e),
                "processed": job.processed,
                "total": job.total,
                "preview_download_path": f"/batch/item/{job.id}/{i}/download",
            })
            continue

        file_name = Path(ref).name
        t0 = time.perf_counter()

        if not pdf_path.is_file():
            duration_ms = int((time.perf_counter() - t0) * 1000)
            empty = {k: None for k in (sample.get("extraction_schema") or {}).keys()}
            filled = {"label": sample.get("label"), "extraction_schema": empty}
            if "pdf_path" in sample: filled["pdf_path"] = sample["pdf_path"]
            if "pdf_filename" in sample: filled["pdf_filename"] = sample["pdf_filename"]
            job.filled_items.append(filled)
            job.meta_items.append({"index": i, "file_name": file_name, "status": "error", "response_ms": duration_ms, "error": f"File not found: {pdf_path}"})
            job.processed += 1
            await job.queue.put({
                "type": "item_error",
                "job_id": job.id,
                "index": i,
                "file_name": file_name,
                "response_ms": duration_ms,
                "error": f"File not found: {pdf_path}",
                "processed": job.processed,
                "total": job.total,
                "preview_download_path": f"/batch/item/{job.id}/{i}/download",
            })
            continue

        try:
            modal_res = await loop.run_in_executor(None, lambda: run_single_infer(sample.get("label"), sample.get("extraction_schema"), str(pdf_path)))
            duration_ms = int((time.perf_counter() - t0) * 1000)
            modal_item = (modal_res or [{}])[0]
            filled = materialize_filled_item(sample, modal_item)

            job.filled_items.append(filled)
            job.meta_items.append({"index": i, "file_name": file_name, "status": "ok", "response_ms": duration_ms})
            job.processed += 1

            await job.queue.put({
                "type": "item_ok",
                "job_id": job.id,
                "index": i,
                "file_name": file_name,
                "response_ms": duration_ms,
                "filled_item": filled,
                "processed": job.processed,
                "total": job.total,
                "preview_download_path": f"/batch/item/{job.id}/{i}/download",
            })
        except Exception as e:
            duration_ms = int((time.perf_counter() - t0) * 1000)
            empty = {k: None for k in (sample.get("extraction_schema") or {}).keys()}
            filled = {"label": sample.get("label"), "extraction_schema": empty}
            if "pdf_path" in sample: filled["pdf_path"] = sample["pdf_path"]
            if "pdf_filename" in sample: filled["pdf_filename"] = sample["pdf_filename"]
            job.filled_items.append(filled)
            job.meta_items.append({"index": i, "file_name": file_name, "status": "error", "response_ms": duration_ms, "error": str(e)})
            job.processed += 1
            await job.queue.put({
                "type": "item_error",
                "job_id": job.id,
                "index": i,
                "file_name": file_name,
                "response_ms": duration_ms,
                "error": str(e),
                "processed": job.processed,
                "total": job.total,
                "preview_download_path": f"/batch/item/{job.id}/{i}/download",
            })

    job.finished_at = time.time()
    await job.queue.put({
        "type": "complete",
        "job_id": job.id,
        "status": job.status,
        "processed": job.processed,
        "failed": len([m for m in job.meta_items if m.get("status") == "error"]),
        "total": job.total,
    })
