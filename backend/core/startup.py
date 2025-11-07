import asyncio, time, logging
from backend.core.config import settings
from backend.clients.modal_client import forward_request

log = logging.getLogger("warmup")

def _warmup_infer() -> None:
    payload = [{
        "label": settings.WARMUP_INFER_LABEL,
        "extraction_schema": settings.WARMUP_INFER_SCHEMA,
        "pdf_path": "WARMUP.pdf",
        "pdf_content": "Warmup ping (ignore this response)"
    }]
    t0 = time.perf_counter()
    try:
        _ = forward_request(
            settings.MODAL_EXTRACTION_URL,
            endpoint="",
            method="POST",
            data=payload,
            timeout=(settings.WARMUP_TIMEOUT_CONNECT, settings.WARMUP_TIMEOUT_READ),
        )
        dt = int((time.perf_counter() - t0) * 1000)
        log.info(f"[warmup] infer ok in {dt} ms (response ignored)")
    except Exception as e:
        dt = int((time.perf_counter() - t0) * 1000)
        log.warning(f"[warmup] infer failed in {dt} ms: {e}")

def _warmup_health() -> None:
    t0 = time.perf_counter()
    try:
        _ = forward_request(
            settings.MODAL_HEALTH_CHECK_URL,
            endpoint=settings.WARMUP_ENDPOINT,
            method="GET",
            timeout=(settings.WARMUP_TIMEOUT_CONNECT, settings.WARMUP_TIMEOUT_READ),
        )
        dt = int((time.perf_counter() - t0) * 1000)
        log.info(f"[warmup] health ok in {dt} ms")
    except Exception as e:
        dt = int((time.perf_counter() - t0) * 1000)
        log.warning(f"[warmup] health failed in {dt} ms: {e}")

def _do_warmup() -> None:
    if not settings.WARMUP_ON_STARTUP:
        return
    if settings.WARMUP_KIND.lower() == "infer":
        _warmup_infer()
    else:
        _warmup_health()

def register_startup_events(app):
    @app.on_event("startup")
    async def _warmup_on_startup():
        loop = asyncio.get_running_loop()
        loop.run_in_executor(None, _do_warmup)  # não bloqueia o boot
