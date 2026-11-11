# Match Link // Company Name Templater

[![CI](https://github.com/jgmchavez-22/Match-Link/actions/workflows/ci.yml/badge.svg)](https://github.com/jgmchavez-22/Match-Link/actions)
[![Python](https://img.shields.io/badge/Python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> An automated data-cleaning and Excel lookup-helper generator that standardizes corporate entity names and dynamically builds prefix-matching formula columns.

---

## Overview

When reconciling customer, vendor, or lead lists across CRM databases, accounting systems, and marketing platforms, differences in legal suffixes (such as `PTE. LTD.`, `LLC`, `Corp`, `Private Limited`) and punctuation prevent clean exact matches (`VLOOKUP`, `XLOOKUP`, `INDEX/MATCH`).

**MatchLink Company Name Templater** is a web application and operational utility powered by **FastAPI** and **Pandas**. It ingests messy company datasets via file upload (`.xlsx`, `.xls`, `.csv`, `.txt`) or direct multi-line text paste, standardizes legal suffix variants, strips non-alphanumeric noise to yield a unified core string, and dynamically appends native Excel formulas for tiered substring matching (`Left 25`, `Left 15`, `Left 10`).

---

## Key Features

- **Legal Entity Standardization & Cleaning:**
  - Standardizes diverse abbreviations and spellings of legal entities (e.g., `P.T.E. L.T.D.`, `PTE LTD`, `PT. LTD.`, `PRIVATE LIMITED` &rarr; `LTD`; `CORPORATION` &rarr; `CORP`).
  - Strips recognized legal suffixes (`LTD`, `LLC`, `INC`, `CORP`, `PLC`, `GMBH`, `CO`, `PT`) and eliminates all non-alphanumeric characters and spaces, outputting a sanitized core name column (`Cleaned Name (exact match, no spaces/chars)`).

- **Dynamic Excel Formula Generation:**
  - Automatically calculates target column letters in Excel and appends formula helper columns:
    - `=LEFT(<Col><Row>, 25)`
    - `=LEFT(<Col><Row>, 15)`
    - `=LEFT(<Col><Row>, 10)`
  - Preserves live formulas in output workbooks for native spreadsheet interoperability.

- **Dual Ingestion Workflows:**
  - **File Upload:** Drag-and-drop or file picker supporting CSV, Excel (`.xlsx`, `.xls`), and plain text (`.txt`).
  - **Text Paste:** Direct multi-line input box for quick ad-hoc lists without prior file saving.

- **Intelligent Header Detection:**
  - Auto-parses spreadsheet headers and selects the best candidate column (matching keywords: `company`, `name`, `firm`, `organization`, `client`, `vendor`, `entity`).

- **Deduplication Toggle:**
  - Option to deduplicate records before templating or preserve all rows in their original sequential order.

- **Export Options:**
  - **Excel Workbook (`.xlsx`):** Formatted sheet with auto-adjusted column widths via OpenPyXL.
  - **CSV Dataset (`.csv`):** Lightweight plain text export for database and ETL ingestion.

- **Memory Safety & Bounded Cache:**
  - Implements `BoundedResultStore` with time-to-live (TTL) eviction and item caps, eliminating memory exhaustion vulnerabilities on sustained workloads.

- **Production Engineering & CI/CD:**
  - Comprehensive `pytest` test suite with 94%+ code coverage.
  - Automated GitHub Actions matrix CI testing Python 3.9, 3.10, 3.11, and 3.12 with `ruff` code formatting and linting.
  - Docker containerization ready for one-command deployment.

---

## Architecture & Technology Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.9+)
- **Server:** [Uvicorn](https://www.uvicorn.org/) ASGI server
- **Data Processing:** [Pandas](https://pandas.pydata.org/) & [OpenPyXL](https://openpyxl.readthedocs.io/)
- **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3 with glassmorphism UI styling
- **CI/CD & Quality:** GitHub Actions, `pytest`, `pytest-cov`, `ruff`
- **Containerization:** Docker & Docker Compose

---

## Quick Start & Installation

### Option 1: Docker (Fastest, zero local dependencies)

```bash
git clone https://github.com/jgmchavez-22/Match-Link.git
cd Match-Link
docker compose up --build
```
Navigate to `http://localhost:8000` in your browser.

---

### Option 2: Local Python Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jgmchavez-22/Match-Link.git
   cd Match-Link
   ```

2. **Run via automated script:**
   - **On macOS/Linux:**
     ```bash
     chmod +x run.sh
     ./run.sh
     ```
   - **On Windows:**
     ```cmd
     run.bat
     ```

3. **Or run manually with virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements-dev.txt
   uvicorn main:app --reload --port 8000
   ```
   Open `http://localhost:8000` in your browser.

---

## Testing & Quality Assurance

The repository includes a comprehensive automated test suite with full coverage of regex tokenization, suffix normalization, formula injection, bounded cache eviction, and API endpoints:

```bash
# Run pytest with code coverage report
pytest --cov=. --cov-report=term-missing

# Run ruff lint and format check
ruff check .
ruff format --check .
```

---

## Project Structure

```
Match-Link/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI matrix workflow (Py 3.9-3.12)
├── tests/
│   ├── __init__.py
│   └── test_templater.py       # Comprehensive pytest test suite (30+ test cases)
├── main.py                     # FastAPI application, cleaning logic, and export endpoints
├── pyproject.toml              # Modern PEP 621 package and tool configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development, testing, and linting dependencies
├── Dockerfile                  # Container build specification
├── docker-compose.yml          # Container compose service
├── run.sh                      # macOS/Linux launcher script
├── run.bat                     # Windows one-click startup script
├── test_templater.py           # Backwards-compatible test runner
├── .gitignore                  # Git ignore rules
├── LICENSE                     # MIT License
├── README.md                   # Project documentation
└── static/
    ├── index.html              # Web application structure
    ├── style.css               # Responsive dark-theme glassmorphism styles
    └── app.js                  # Client-side state, drag-and-drop, and API integration
```

---

## Author & Attribution

Developed by **Jan Gabriel Chavez** ([@jgmchavez-22](https://github.com/jgmchavez-22)).  
Database Management & Workflow Automation Specialist.
