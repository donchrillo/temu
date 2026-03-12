from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from config import OUTPUT_DIR
from backend.schemas import FileListResponse, FileContentResponse
from backend.services.file_service import list_files, _validate_filename

router = APIRouter(prefix="/api/exports", tags=["exports"])


@router.get("", response_model=FileListResponse)
def list_exports():
    return {"files": list_files(OUTPUT_DIR)}


@router.get("/{filename}/content", response_model=FileContentResponse)
def get_export_content(filename: str):
    safe_name = _validate_filename(filename)
    path = OUTPUT_DIR / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    content = path.read_text(encoding="utf-8", errors="replace")
    return {"status": "ok", "filename": safe_name, "content": content}


@router.get("/{filename}")
def download_export(filename: str):
    safe_name = _validate_filename(filename)
    path = OUTPUT_DIR / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, filename=safe_name)
