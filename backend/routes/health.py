import time
from fastapi import APIRouter, HTTPException
from backend.core.config import settings
from backend.core.responses import pretty_response
from backend.core.health_utils import local_health_payload
from backend.clients.modal_client import forward_request

router = APIRouter()

@router.get("/health/local")
def health_local():
    return pretty_response(local_health_payload())

@router.get("/health/remote")
def health_remote():
    if not settings.REMOTE_ENABLED:
        raise HTTPException(status_code=503, detail="Remote health not configured.")
    t0 = time.perf_counter()
    remote = forward_request(settings.MODAL_HEALTH_CHECK_URL, method="GET")
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return pretty_response({"status": "ok", "latency_ms": latency_ms, "remote": remote})

@router.get("/health")
def health_combined():
    local_status = local_health_payload()
    if settings.REMOTE_ENABLED:
        try:
            t0 = time.perf_counter()
            remote = forward_request(settings.MODAL_HEALTH_CHECK_URL, method="GET")
            latency_ms = int((time.perf_counter() - t0) * 1000)
            remote_status = {"status": "ok", "latency_ms": latency_ms, "remote": remote}
        except HTTPException as e:
            remote_status = {"status": "error", "error": e.detail}
    else:
        remote_status = {"status": "unconfigured"}
    return pretty_response({"local_status": "ok", "remote_status": remote_status, "local": local_status})
