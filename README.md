# MatchLink // Company Name Templater

> An automated data-cleaning and Excel lookup-helper generator that standardizes corporate entity names and dynamically builds prefix-matching formula columns.

---

## Overview

When reconciling customer, vendor, or lead lists across CRM databases, accounting systems, and marketing platforms, differences in legal suffixes (such as `PTE. LTD.`, `LLC`, `Corp`, `Private Limited`) and punctuation prevent clean exact matches (`VLOOKUP`, `XLOOKUP`, `INDEX/MATCH`).

**MatchLink Company Name Templater** is a local web application powered by **FastAPI** and **Pandas**. It ingests messy company datasets via file upload (`.xlsx`, `.xls`, `.csv`, `.txt`) or direct multi-line text paste, standardizes legal suffix variants, strips non-alphanumeric noise to yield a unified core string, and dynamically appends native Excel formulas for tiered substring matching (`Left 25`, `Left 15`, `Left 10`).

---

## Implemented Features

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

- **Automated Test Suite:**
  - Unit tests covering regex tokenization, suffix normalization, formula row offsetting, and REST API endpoints.

---

## Architecture & Technology Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.8+)
- **Server:** [Uvicorn](https://www.uvicorn.org/) ASGI server
- **Data Processing:** [Pandas](https://pandas.pydata.org/) & [OpenPyXL](https://openpyxl.readthedocs.io/)
- **Frontend:** Vanilla JavaScript (ES6+), HTML5, CSS3 with glassmorphism UI styling
- **Icons & Fonts:** FontAwesome 6, Google Fonts (Outfit)

---

## Prerequisites

- **Python 3.8** or higher
- `pip` (Python package installer)
- Modern web browser (Chrome, Edge, Firefox)

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jgmchavez-22/company-name-templater.git
   cd company-name-templater
   ```

2. **Create and activate a virtual environment (recommended):**
   - On Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Application

### Option 1: One-Click Startup (Windows)
Run the provided batch script from the project folder:
```cmd
run.bat
```
The script will:
1. Verify Python availability on `PATH`.
2. Check and install missing dependencies from `requirements.txt`.
3. Open your default browser to `http://localhost:8001`.
4. Launch the FastAPI server with auto-reload enabled.

### Option 2: Manual CLI Launch
Start the server directly using Uvicorn:
```bash
python -m uvicorn main:app --port 8001 --reload
```
Once started, navigate to:
```
http://localhost:8001
```

---

## Configuration & Environment Variables

No external API keys or `.env` variables are required. The server runs self-contained on localhost (`http://localhost:8001`).

---

## Testing

The project includes unit and endpoint tests in `test_templater.py`.

Run the test suite:
```bash
python test_templater.py
```

The test script validates:
1. Suffix standardization (e.g. `PTE. LTD.` &rarr; `LTD`, `PT. L.T.D.` &rarr; `LTD`).
2. Company name cleaning and whitespace/punctuation elimination.
3. Column index calculation and Excel formula string generation.
4. Header parsing endpoint (`/api/parse-headers`).
5. Templating and export logic with both deduplication enabled and disabled (`/api/template`).

---

## Project Structure

```
company-name-templater/
├── main.py              # FastAPI application, cleaning logic, and export endpoints
├── requirements.txt     # Python package dependencies
├── run.bat              # Windows one-click startup batch script
├── test_templater.py    # Unit and API integration test suite
├── .gitignore           # Git ignore rules for Python, cache, and OS artifacts
├── README.md            # Project documentation
└── static/
    ├── index.html       # Web application structure
    ├── style.css        # Responsive dark-theme glassmorphism styles
    └── app.js           # Client-side state, drag-and-drop, and API integration
```

---

## Known Limitations

- In-memory results store: Processed files are cached in server memory (`results_store`) keyed by UUID and removed upon download. For high-volume multi-user production environments, a persistent storage or Redis cache layer would be recommended.
- Standalone execution: Designed for local desktop or internal operations server use; authentication and multi-tenancy are not implemented.

---

## Author & Attribution

Developed by **Jan Gabriel Chavez** ([@jgmchavez-22](https://github.com/jgmchavez-22)).
