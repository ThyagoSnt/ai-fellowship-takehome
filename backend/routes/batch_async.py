import json
import uuid
import asyncio
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.core.config import settings
from backend.core.responses import pretty_response, pretty_download
from backend.core.sse import sse_format
from backend.schemas.v1.schemas import BatchRequest
from backend.models.job_model import BatchJob, JOBS
from backend.services.batch_runner import run_batch_job

router = APIRouter()

@router.post("/batch/start")
async def batch_start(request: BatchRequest):
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

    job_id = uuid.uuid4().hex
    job = BatchJob(id=job_id, total=len(dataset))
    JOBS[job_id] = job
    asyncio.create_task(run_batch_job(job, dataset, root))
    return {"status": "started", "job_id": job_id, "total": job.total}

@router.get("/batch/stream/{job_id}")
async def batch_stream(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")

    async def event_generator():
        yield "retry: 1500\n\n"
        while True:
            item = await job.queue.get()
            yield sse_format(item)
            if item.get("type") == "complete":
                break

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(event_generator(), media_type="text/event-stream", headers=headers)

@router.get("/batch/result/{job_id}")
def batch_result(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return pretty_response(job.filled_items)

@router.get("/batch/result/{job_id}/download")
def batch_result_download(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return pretty_download(job.filled_items, filename="batch_result.json")

@router.get("/batch/item/{job_id}/{index}")
def batch_item(job_id: str, index: int):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    if index < 0 or index >= len(job.filled_items):
        raise HTTPException(status_code=404, detail="Item index out of range")
    meta = next((m for m in job.meta_items if m["index"] == index), None)
    file_name = (meta or {}).get("file_name")
    payload = {
        "file_name": file_name,
        "item": job.filled_items[index],
    }
    return pretty_response(payload)

@router.get("/batch/item/{job_id}/{index}/download")
def batch_item_download(job_id: str, index: int):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    if index < 0 or index >= len(job.filled_items):
        raise HTTPException(status_code=404, detail="Item index out of range")
    item = job.filled_items[index]
    filename = f"preview_{index}_result.json"
    return pretty_download(item, filename=filename)

@router.get("/batch/meta/{job_id}")
def batch_meta(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    return pretty_response(job.meta_items)
