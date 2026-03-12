from __future__ import annotations

from fastapi import APIRouter, UploadFile, File

from config import INPUT_DIR_BESTELLUNGEN, INPUT_DIR_ZAHLUNGEN
from backend.schemas import (
    FileListResponse,
    UploadResponse,
    FileContentResponse,
    SaveFileContentRequest,
)
from backend.services.file_service import (
    list_files,
    save_upload,
    read_file_content,
    write_file_content,
)

router = APIRouter(prefix="/api/files", tags=["files"])


@router.get("/orders", response_model=FileListResponse)
def list_order_files():
    return {"files": list_files(INPUT_DIR_BESTELLUNGEN)}


@router.get("/payments", response_model=FileListResponse)
def list_payment_files():
    return {"files": list_files(INPUT_DIR_ZAHLUNGEN)}


@router.post("/orders/upload", response_model=UploadResponse)
def upload_order_file(file: UploadFile = File(...)):
    filename = save_upload(file, INPUT_DIR_BESTELLUNGEN)
    return {"status": "ok", "filename": filename}


@router.post("/payments/upload", response_model=UploadResponse)
def upload_payment_file(file: UploadFile = File(...)):
    filename = save_upload(file, INPUT_DIR_ZAHLUNGEN)
    return {"status": "ok", "filename": filename}


@router.get("/orders/{filename}/content", response_model=FileContentResponse)
def get_order_file_content(filename: str):
    content = read_file_content(INPUT_DIR_BESTELLUNGEN, filename)
    return {"status": "ok", "filename": filename, "content": content}


@router.put("/orders/{filename}/content", response_model=UploadResponse)
def save_order_file_content(filename: str, payload: SaveFileContentRequest):
    saved = write_file_content(INPUT_DIR_BESTELLUNGEN, filename, payload.content)
    return {"status": "ok", "filename": saved}


@router.get("/payments/{filename}/content", response_model=FileContentResponse)
def get_payment_file_content(filename: str):
    content = read_file_content(INPUT_DIR_ZAHLUNGEN, filename)
    return {"status": "ok", "filename": filename, "content": content}


@router.put("/payments/{filename}/content", response_model=UploadResponse)
def save_payment_file_content(filename: str, payload: SaveFileContentRequest):
    saved = write_file_content(INPUT_DIR_ZAHLUNGEN, filename, payload.content)
    return {"status": "ok", "filename": saved}
