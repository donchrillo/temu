from __future__ import annotations

from fastapi import APIRouter

from backend.schemas import OpAnalysisResponse
from backend.services.conversion_service import run_op_analysis

router = APIRouter(prefix="/api/op", tags=["op"])


@router.post("/analyze", response_model=OpAnalysisResponse)
def analyze_op():
    result = run_op_analysis()
    return {
        "status": "ok",
        "message": result["message"],
        "output_files": result["output_files"],
        "summary": result.get("summary"),
    }
