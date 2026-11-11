"""
Company Name Templater API
Automated legal entity standardizer and Excel lookup helper generator.
"""

from __future__ import annotations

import io
import re
import time
import uuid
from collections import OrderedDict
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="Company Name Templater API",
    version="1.0.0",
    description=(
        "Automated legal entity standardizer and Excel lookup helper "
        "generator built with FastAPI and Pandas."
    ),
)

# Enable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BoundedResultStore:
    """Thread-safe bounded in-memory store with TTL to prevent memory exhaustion."""

    def __init__(self, max_items: int = 100, ttl_seconds: int = 1800) -> None:
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        self._store: OrderedDict[str, dict[str, Any]] = OrderedDict()

    def _evict_expired(self) -> None:
        now = time.time()
        expired = [
            k
            for k, v in self._store.items()
            if now - v.get("created_at", 0) > self.ttl_seconds
        ]
        for k in expired:
            self._store.pop(k, None)

    def set(self, key: str, data: bytes, fmt: str) -> None:
        self._evict_expired()
        if len(self._store) >= self.max_items:
            self._store.popitem(last=False)
        self._store[key] = {
            "data": data,
            "format": fmt,
            "created_at": time.time(),
        }

    def pop(self, key: str) -> dict[str, Any] | None:
        self._evict_expired()
        return self._store.pop(key, None)

    def __contains__(self, key: str) -> bool:
        self._evict_expired()
        return key in self._store


# Global store for processed files (bounded to 100 items, 30 min TTL)
results_store = BoundedResultStore(max_items=100, ttl_seconds=1800)


def standardize_legal_suffixes(name: Any) -> str:
    """
    Normalizes variations of legal entities (dots, spaces, spelling):
    - Normalizes dots/spaces in abbreviations (e.g. P.T.E. L.T.D. -> PTE LTD)
    - Normalizes various forms (PTE LTD, PRIVATE LIMITED, etc.) to standard: LTD.
    - Normalizes CORPORATION -> CORP, etc.
    """
    if pd.isna(name) or not isinstance(name, str):
        return ""

    val = str(name).upper()

    # Normalize common abbreviations with spaces/dots to standardized tokens
    val = re.sub(r"\bP\.?\s*T\.?\s*E\.?\s*L\.?\s*T\.?\s*D\b\.?", "PTE LTD", val)
    val = re.sub(r"\bP\.?\s*T\.?\s*L\.?\s*T\.?\s*D\b\.?", "PT LTD", val)
    val = re.sub(r"\bP\.?\s*V\.?\s*T\.?\s*L\.?\s*T\.?\s*D\b\.?", "PVT LTD", val)
    val = re.sub(r"\bC\.?\s*O\.?\s*L\.?\s*T\.?\s*D\b\.?", "CO LTD", val)
    val = re.sub(r"\bL\.?\s*T\.?\s*D\b\.?", "LTD", val)
    val = re.sub(r"\bL\.?\s*L\.?\s*C\b\.?", "LLC", val)
    val = re.sub(r"\bI\.?\s*N\.?\s*C\b\.?", "INC", val)
    val = re.sub(r"\bC\.?\s*O\.?\s*R\.?\s*P\b\.?", "CORP", val)
    val = re.sub(r"\bP\.?\s*L\.?\s*C\b\.?", "PLC", val)
    val = re.sub(r"\bG\.?\s*M\.?\s*B\.?\s*H\b\.?", "GMBH", val)
    val = re.sub(r"\bP\.?\s*T\b\.?", "PT", val)
    val = re.sub(r"\bC\.?\s*O\b\.?", "CO", val)

    # Normalize standard variations to LTD
    val = re.sub(
        r"\b(PRIVATE LIMITED|PVT LTD|PTE LTD|PT LTD|CO LTD|LIMITED)\b", "LTD", val
    )
    val = re.sub(r"\bCORPORATION\b", "CORP", val)

    return val


def clean_company_name(name: Any) -> str:
    """
    Standardizes company names by converting to uppercase, standardizing legal suffixes
    to standard representations, stripping common legal suffixes, and removing all
    spaces and non-alphanumeric characters.
    """
    if pd.isna(name) or not isinstance(name, str):
        return ""

    # Standardize legal suffixes first
    name_clean = standardize_legal_suffixes(name)

    # Replace non-alphanumeric and non-space characters with space
    name_clean = re.sub(r"[^A-Z0-9\s]", " ", name_clean)

    # Normalize spaces
    name_clean = re.sub(r"\s+", " ", name_clean).strip()

    # Suffix patterns with word boundaries
    suffixes = [
        r"\bLTD\b",
        r"\bLLC\b",
        r"\bINC\b",
        r"\bCORP\b",
        r"\bPLC\b",
        r"\bGMBH\b",
        r"\bCO\b",
        r"\bPT\b",
    ]
    for pattern in suffixes:
        name_clean = re.sub(pattern, "", name_clean)

    # Strip all remaining spaces and non-alphanumeric characters
    name_clean = re.sub(r"[^A-Z0-9]", "", name_clean)
    return name_clean


def get_file_type(file_name: str | None, content_type: str = "") -> str:
    file_name = (file_name or "").lower()
    content_type = (content_type or "").lower()

    ext = file_name.split(".")[-1] if "." in file_name else ""
    if ext == "csv" or "csv" in content_type:
        return "csv"
    elif ext in ["xlsx", "xls"] or "sheet" in content_type or "excel" in content_type:
        return "excel"
    elif (
        ext == "txt"
        or "text" in content_type
        or "plain" in content_type
        or file_name == "blob"
    ):
        return "text"
    return "text"


def parse_headers(
    file_bytes: bytes, file_name: str | None, content_type: str = ""
) -> list[str]:
    ftype = get_file_type(file_name, content_type)
    if ftype == "csv":
        df = pd.read_csv(io.BytesIO(file_bytes), nrows=2)
    elif ftype == "excel":
        df = pd.read_excel(io.BytesIO(file_bytes), nrows=2)
    elif ftype == "text":
        df = pd.DataFrame(columns=["Company Name"])
    else:
        raise ValueError("Unsupported file format. Please upload CSV, Excel, or TXT.")
    return [str(col) for col in df.columns]


def load_dataframe(
    file_bytes: bytes, file_name: str | None, content_type: str = ""
) -> pd.DataFrame:
    ftype = get_file_type(file_name, content_type)
    if ftype == "csv":
        return pd.read_csv(io.BytesIO(file_bytes))
    elif ftype == "excel":
        return pd.read_excel(io.BytesIO(file_bytes))
    elif ftype == "text":
        text = file_bytes.decode("utf-8", errors="ignore")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return pd.DataFrame({"Company Name": lines})
    else:
        raise ValueError("Unsupported file format. Please upload CSV, Excel, or TXT.")


def get_column_letter(col_idx: int) -> str:
    """
    Converts a 1-based column index to an Excel column letter (e.g., 1 -> A, 27 -> AA).
    """
    letter = ""
    while col_idx > 0:
        col_idx, remainder = divmod(col_idx - 1, 26)
        letter = chr(65 + remainder) + letter
    return letter


@app.post("/api/parse-headers")
async def api_parse_headers(file: UploadFile = File(...)) -> dict[str, list[str]]:
    try:
        content = await file.read()
        headers = parse_headers(content, file.filename, file.content_type or "")
        return {"headers": headers}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing headers: {str(e)}")


@app.post("/api/template")
async def api_template(
    file: UploadFile = File(...),
    company_col: str = Form(...),
    export_format: str = Form("excel"),
    deduplicate: bool = Form(True),
) -> dict[str, Any]:
    try:
        content = await file.read()
        df = load_dataframe(content, file.filename, file.content_type or "")

        if company_col not in df.columns:
            if "Company Name" in df.columns:
                company_col = "Company Name"
            else:
                available = list(df.columns)
                raise ValueError(
                    f"Column '{company_col}' not found in file. Available: {available}"
                )

        if deduplicate:
            df = df.drop_duplicates().reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)

        cleaned_col_name = "Cleaned Name (exact match, no spaces/chars)"
        df[cleaned_col_name] = df[company_col].apply(clean_company_name)

        cleaned_col_idx = list(df.columns).index(cleaned_col_name) + 1
        col_letter = get_column_letter(cleaned_col_idx)

        df["by Left 25 Characters"] = [
            f"=LEFT({col_letter}{i}, 25)" for i in range(2, len(df) + 2)
        ]
        df["by Left 15 Characters"] = [
            f"=LEFT({col_letter}{i}, 15)" for i in range(2, len(df) + 2)
        ]
        df["by Left 10 Characters"] = [
            f"=LEFT({col_letter}{i}, 10)" for i in range(2, len(df) + 2)
        ]

        download_id = str(uuid.uuid4())

        if export_format == "csv":
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue().encode("utf-8")
            results_store.set(download_id, csv_data, "csv")
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name="Templated List", index=False)
                workbook = writer.book
                worksheet = workbook["Templated List"]
                for col in worksheet.columns:
                    max_len = max(len(str(val or "")) for val in col)
                    col_letter = col[0].column_letter
                    worksheet.column_dimensions[col_letter].width = max(max_len + 3, 10)

            output.seek(0)
            results_store.set(download_id, output.getvalue(), "excel")

        return {
            "download_id": download_id,
            "total_records": len(df),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Templating failed: {str(e)}")


@app.get("/api/download/{download_id}")
async def api_download(download_id: str) -> StreamingResponse:
    stored = results_store.pop(download_id)
    if not stored:
        raise HTTPException(
            status_code=404,
            detail="File has expired or is invalid. Please run the templater again.",
        )

    file_bytes: bytes = stored["data"]
    fmt: str = stored["format"]

    if fmt == "csv":
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=templated_companies.csv"
            },
        )
    else:
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=templated_companies.xlsx"
            },
        )


# Serve frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root() -> FileResponse:
    return FileResponse("static/index.html")
