import json
from typing import Any
from fastapi.responses import Response

def pretty_response(payload: Any) -> Response:
    return Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
    )

def pretty_download(payload: Any, filename: str) -> Response:
    resp = Response(
        content=json.dumps(payload, indent=2, ensure_ascii=False),
        media_type="application/json",
    )
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp
