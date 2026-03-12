from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional


class FileInfo(BaseModel):
    name: str
    size: int
    modified: datetime


class FileListResponse(BaseModel):
    files: List[FileInfo]


class UploadResponse(BaseModel):
    status: str = Field(default="ok")
    filename: str


class FileContentResponse(BaseModel):
    status: str = Field(default="ok")
    filename: str
    content: str


class SaveFileContentRequest(BaseModel):
    content: str


class ConvertRequest(BaseModel):
    files: List[str]


class ConvertFileDetail(BaseModel):
    filename: str
    records: int
    bookings: int
    skipped: int = 0
    ignored: int = 0


class ConvertIgnoredRow(BaseModel):
    filename: str
    bestellnummer: str
    rechnungsnummer: str
    verkaufsart: str
    grund: str


class ConvertDetails(BaseModel):
    mode: str
    files: List[ConvertFileDetail]
    notes: List[str] = []
    ignored_rows: List[ConvertIgnoredRow] = []


class ConvertResult(BaseModel):
    status: str = Field(default="ok")
    message: str
    processed_files: List[str]
    totals: dict
    output_files: List[str]
    details: Optional[ConvertDetails] = None


class OffenerPosten(BaseModel):
    belegfeld1: str
    saldo: float


class OpSummary(BaseModel):
    ausgeglichen_count: int
    bestellungen_ohne_zahlung: int
    zahlungen_ohne_bestellung: int
    gesamt_offen_eur: float
    ohne_op_count: int
    top_offen: List[OffenerPosten]


class OpAnalysisResponse(BaseModel):
    status: str = Field(default="ok")
    message: str
    output_files: List[str]
    summary: Optional[OpSummary] = None
