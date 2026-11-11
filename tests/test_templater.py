"""
Comprehensive automated test suite for Match-Link.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import (
    BoundedResultStore,
    app,
    clean_company_name,
    get_column_letter,
    get_file_type,
    load_dataframe,
    parse_headers,
    standardize_legal_suffixes,
)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


# ==========================================
# Unit Tests: Normalization & Cleaning
# ==========================================


@pytest.mark.parametrize(
    "raw_input,expected_output",
    [
        ("PTE. LTD.", "LTD"),
        ("PT. L.T.D.", "LTD"),
        ("PRIVATE LIMITED", "LTD"),
        ("Google LLC", "GOOGLE LLC"),
        ("Tesla, Inc.", "TESLA, INC"),
        ("Microsoft Corporation", "MICROSOFT CORP"),
        ("Siemens GmbH", "SIEMENS GMBH"),
        ("Barclays PLC", "BARCLAYS PLC"),
        (None, ""),
        ("", ""),
    ],
)
def test_suffix_standardization(raw_input: str | None, expected_output: str) -> None:
    assert standardize_legal_suffixes(raw_input) == expected_output


@pytest.mark.parametrize(
    "raw_input,expected_clean",
    [
        ("Google LLC", "GOOGLE"),
        ("Tesla, Inc.", "TESLA"),
        ("Microsoft Corporation", "MICROSOFT"),
        ("Standard Chartered Pte Ltd", "STANDARDCHARTERED"),
        ("PT. ABC Indonesia", "ABCINDONESIA"),
        ("PTE. LTD.", ""),
        ("Company PTE. LTD.", "COMPANY"),
        ("Random Entity", "RANDOMENTITY"),
        (None, ""),
        ("", ""),
    ],
)
def test_company_name_cleaning(raw_input: str | None, expected_clean: str) -> None:
    assert clean_company_name(raw_input) == expected_clean


def test_get_column_letter() -> None:
    assert get_column_letter(1) == "A"
    assert get_column_letter(2) == "B"
    assert get_column_letter(26) == "Z"
    assert get_column_letter(27) == "AA"
    assert get_column_letter(28) == "AB"


def test_file_type_detection() -> None:
    assert get_file_type("data.csv") == "csv"
    assert get_file_type("sheet.xlsx") == "excel"
    assert get_file_type("notes.txt") == "text"
    assert get_file_type("unknown.bin") == "text"


def test_parse_headers_csv() -> None:
    csv_bytes = b"ID,Company Name,Country\n1,Acme Corp,USA\n"
    headers = parse_headers(csv_bytes, "test.csv", "text/csv")
    assert headers == ["ID", "Company Name", "Country"]


def test_load_dataframe_text() -> None:
    txt_bytes = b"Acme Corp\nGlobex LLC\nInitech\n"
    df = load_dataframe(txt_bytes, "names.txt", "text/plain")
    assert list(df.columns) == ["Company Name"]
    assert len(df) == 3


# ==========================================
# Unit Tests: BoundedResultStore Cache
# ==========================================


def test_bounded_result_store() -> None:
    store = BoundedResultStore(max_items=3, ttl_seconds=10)
    store.set("key1", b"data1", "csv")
    store.set("key2", b"data2", "csv")
    store.set("key3", b"data3", "csv")

    assert "key1" in store
    assert "key2" in store
    assert "key3" in store

    # Adding a 4th item evicts the oldest (key1)
    store.set("key4", b"data4", "csv")
    assert "key1" not in store
    assert "key4" in store

    # Pop item
    val = store.pop("key4")
    assert val is not None
    assert val["data"] == b"data4"
    assert "key4" not in store


def test_bounded_result_store_ttl() -> None:
    store = BoundedResultStore(max_items=5, ttl_seconds=0.01)
    store.set("temp", b"data", "csv")
    import time

    time.sleep(0.02)
    assert store.pop("temp") is None


# ==========================================
# Integration Tests: FastAPI Endpoints
# ==========================================


def test_api_parse_headers_endpoint(client: TestClient) -> None:
    csv_bytes = b"Company ID,Company Name,Website\nC01,Google LLC,google.com\n"
    response = client.post(
        "/api/parse-headers",
        files={"file": ("companies.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "headers" in data
    assert data["headers"] == ["Company ID", "Company Name", "Website"]


def test_api_template_excel_and_csv(client: TestClient) -> None:
    csv_bytes = (
        b"Company Name,Website\n"
        b"Google LLC,google.com\n"
        b"Tesla Inc,tesla.com\n"
        b"Google LLC,google.com\n"
    )

    # 1. Excel export with deduplication
    res_excel = client.post(
        "/api/template",
        files={"file": ("companies.csv", csv_bytes, "text/csv")},
        data={
            "company_col": "Company Name",
            "export_format": "excel",
            "deduplicate": "true",
        },
    )
    assert res_excel.status_code == 200
    data_excel = res_excel.json()
    assert "download_id" in data_excel
    assert data_excel["total_records"] == 2

    # Download Excel file
    dl_excel = client.get(f"/api/download/{data_excel['download_id']}")
    assert dl_excel.status_code == 200
    assert "spreadsheetml" in dl_excel.headers["content-type"]

    # 2. CSV export without deduplication
    res_csv = client.post(
        "/api/template",
        files={"file": ("companies.csv", csv_bytes, "text/csv")},
        data={
            "company_col": "Company Name",
            "export_format": "csv",
            "deduplicate": "false",
        },
    )
    assert res_csv.status_code == 200
    data_csv = res_csv.json()
    assert data_csv["total_records"] == 3

    # Download CSV file
    dl_csv = client.get(f"/api/download/{data_csv['download_id']}")
    assert dl_csv.status_code == 200
    assert "text/csv" in dl_csv.headers["content-type"]
    assert b"Cleaned Name (exact match, no spaces/chars)" in dl_csv.content


def test_api_download_expired_404(client: TestClient) -> None:
    response = client.get("/api/download/non-existent-uuid")
    assert response.status_code == 404
    assert "expired or is invalid" in response.json()["detail"]


def test_api_template_invalid_column(client: TestClient) -> None:
    csv_bytes = b"ColA,ColB\n1,2\n"
    response = client.post(
        "/api/template",
        files={"file": ("test.csv", csv_bytes, "text/csv")},
        data={"company_col": "NonExistentCol", "export_format": "csv"},
    )
    assert response.status_code == 400
    assert "not found in file" in response.json()["detail"]
