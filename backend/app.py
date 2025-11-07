#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.core.config import settings
from backend.routes import health, infer, batch_sync, batch_async
from backend.core.startup import register_startup_events


app = FastAPI(title="Local Proxy for Modal Document Parsing API", version=settings.APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(infer.router)
app.include_router(batch_sync.router)
app.include_router(batch_async.router)
register_startup_events(app)

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8000
    print(f"\nServer running at: http://{host}:{port}")
    print(f"Docs available at: http://localhost:{port}/docs\n")
    uvicorn.run(app, host=host, port=port)
