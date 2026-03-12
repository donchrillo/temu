from __future__ import annotations

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.routers import files, convert, exports, op  # noqa: E402

app = FastAPI(title="Temu DATEV Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files.router)
app.include_router(convert.router)
app.include_router(op.router)
app.include_router(exports.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
