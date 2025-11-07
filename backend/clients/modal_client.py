import os
from typing import Any, Dict
import requests
from fastapi import HTTPException
from backend.core.config import settings

AUTH_HEADER_NAME = os.getenv("AUTH_HEADER_NAME", "Authorization")
AUTH_SCHEME = os.getenv("AUTH_SCHEME", "Bearer")

def forward_request(base_url: str | None, endpoint: str = "", data: Any = None,
                    method: str = "POST", timeout: float | tuple[float,float] | None = None) -> Any:
    if not base_url:
        raise HTTPException(status_code=503, detail="Remote base URL not configured.")
    url = base_url.rstrip("/") + endpoint
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout or 60) if method.upper()=="GET" \
            else requests.post(url, json=data, headers=headers, timeout=timeout or 180)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError:
            return {"status_code": r.status_code, "text": r.text}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Error contacting {url}: {e}")
