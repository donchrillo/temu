from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile


ALLOWED_EXTENSIONS = {".csv"}


def _validate_filename(name: str) -> str:
    if not name or name.startswith("."):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name


def list_files(directory: Path) -> List[dict]:
    directory.mkdir(parents=True, exist_ok=True)
    files = []
    for path in sorted(directory.glob("*") ):
        if path.is_file():
            stat = path.stat()
            files.append(
                {
                    "name": path.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                }
            )
    return files


def save_upload(upload: UploadFile, directory: Path) -> str:
    filename = _validate_filename(upload.filename or "")
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported")

    directory.mkdir(parents=True, exist_ok=True)
    target_path = directory / filename

    with target_path.open("wb") as f:
        content = upload.file.read()
        f.write(content)

    return target_path.name


def ensure_files_exist(directory: Path, filenames: List[str]) -> List[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    if not filenames:
        raise HTTPException(status_code=400, detail="No files selected")

    paths: List[Path] = []
    for name in filenames:
        safe_name = _validate_filename(name)
        path = directory / safe_name
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=404, detail=f"File not found: {safe_name}")
        paths.append(path)
    return paths


def read_file_content(directory: Path, filename: str) -> str:
    safe_name = _validate_filename(filename)
    path = directory / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {safe_name}")

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV files can be opened")

    return path.read_text(encoding="utf-8")


def write_file_content(directory: Path, filename: str, content: str) -> str:
    safe_name = _validate_filename(filename)
    path = directory / safe_name
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {safe_name}")

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only CSV files can be saved")

    path.write_text(content, encoding="utf-8")
    return path.name
