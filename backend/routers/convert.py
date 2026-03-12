from __future__ import annotations

from fastapi import APIRouter

from config import INPUT_DIR_BESTELLUNGEN, INPUT_DIR_ZAHLUNGEN
from backend.schemas import ConvertRequest, ConvertResult
from backend.services.file_service import ensure_files_exist
from backend.services.conversion_service import convert_orders, convert_payments

router = APIRouter(prefix="/api/convert", tags=["convert"])


@router.post("/orders", response_model=ConvertResult)
def convert_orders_endpoint(payload: ConvertRequest):
    files = ensure_files_exist(INPUT_DIR_BESTELLUNGEN, payload.files)
    result = convert_orders(files)
    return {
        "status": "ok",
        "message": result["message"],
        "processed_files": [p.name for p in files],
        "totals": result["totals"],
        "output_files": result["output_files"],
        "details": result.get("details"),
    }


@router.post("/payments", response_model=ConvertResult)
def convert_payments_endpoint(payload: ConvertRequest):
    files = ensure_files_exist(INPUT_DIR_ZAHLUNGEN, payload.files)
    result = convert_payments(files)
    return {
        "status": "ok",
        "message": result["message"],
        "processed_files": [p.name for p in files],
        "totals": result["totals"],
        "output_files": result["output_files"],
        "details": result.get("details"),
    }
