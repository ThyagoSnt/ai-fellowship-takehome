import time
from typing import Dict, Any
from backend.core.config import settings

def local_health_payload() -> Dict[str, Any]:
    uptime_s = int(time.time() - settings.PROCESS_START_TIME)
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "uptime_s": uptime_s,
        "env_ready": {
            "MODAL_EXTRACTION_URL": bool(settings.MODAL_EXTRACTION_URL),
            "MODAL_HEALTH_CHECK_URL": bool(settings.MODAL_HEALTH_CHECK_URL),
        },
    }
