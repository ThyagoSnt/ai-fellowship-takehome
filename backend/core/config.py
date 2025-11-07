import os, time, json
from dataclasses import dataclass
from dotenv import load_dotenv
load_dotenv()

def _as_bool(v: str | None, default: bool) -> bool:
    if v is None: return default
    return v.strip().lower() in ("1","true","yes","on")

@dataclass
class Settings:
    APP_VERSION: str = "1.6.2"
    MODAL_EXTRACTION_URL: str | None = os.getenv("MODAL_EXTRACTION_URL")
    MODAL_HEALTH_CHECK_URL: str | None = os.getenv("MODAL_HEALTH_CHECK_URL")
    PROCESS_START_TIME: float = time.time()

    # warmup
    WARMUP_ON_STARTUP: bool = _as_bool(os.getenv("WARMUP_ON_STARTUP", "true"), True)
    WARMUP_KIND: str = os.getenv("WARMUP_KIND", "infer")
    WARMUP_ENDPOINT: str = os.getenv("WARMUP_ENDPOINT", "/health")
    WARMUP_TIMEOUT_CONNECT: float = float(os.getenv("WARMUP_TIMEOUT_CONNECT", "5"))
    WARMUP_TIMEOUT_READ: float = float(os.getenv("WARMUP_TIMEOUT_READ", "10"))

    # warmup via infer
    WARMUP_INFER_LABEL: str = os.getenv("WARMUP_INFER_LABEL", "warmup")
    WARMUP_INFER_SCHEMA_JSON: str = os.getenv("WARMUP_INFER_SCHEMA_JSON", '{"warmup": ""}')
    @property
    def WARMUP_INFER_SCHEMA(self) -> dict:
        try:
            return json.loads(self.WARMUP_INFER_SCHEMA_JSON)
        except Exception:
            return {"warmup": ""}

    @property
    def REMOTE_ENABLED(self) -> bool:
        return bool(self.MODAL_EXTRACTION_URL and self.MODAL_HEALTH_CHECK_URL)

settings = Settings()
