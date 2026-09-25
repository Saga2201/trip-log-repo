# Invoices Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an Invoices section to the JB Transport app that generates three linked billing PDFs (LR, Party Bill, Driver Bill) from a single form, sharing one financial-year-scoped serial number and stored so they can be edited and regenerated.

**Architecture:** React + FastAPI + SQLite (matches current stack). One flat `invoices` table plus a small `invoice_sequences` helper for atomic serial allocation. PDFs are HTML/CSS templates rendered by WeasyPrint. Static company info lives in a Python constants module.

**Tech Stack:** Python 3, FastAPI, SQLite, WeasyPrint, Jinja2, `num2words`, React, react-router-dom, TailwindCSS, lucide-react, axios.

## Global Constraints

- Spec source of truth: `docs/superpowers/specs/2026-09-25-invoices-design.md`. Every task's behavior implicitly matches the spec.
- Invoices are **standalone** — no `trip_id` column, no linkage to the `trips` table.
- Serial format: `JB/YY-YY/NNN`, zero-padded to 3 digits, per-FY (Apr–Mar). Immutable after allocation.
- All bill labels/text on PDFs are **English only**.
- Every PDF template reserves a `~60×60 px` `qr-slot` div in the header. No live QR encoding this iteration.
- Company constants (name, address, phones, GST) come from `backend/pdf/company.py`, never from the DB.
- Follow existing patterns: React modal shell mirrors `TripModal.jsx`; backend routes mirror `backend/api.py` conventions.
- Additive DB migrations only via `database.init_db()` — do not touch the `trips` table.
- Frequent commits: at least one commit per task.

---

## File Structure

**New files**

```
backend/pdf/__init__.py
backend/pdf/company.py                    # COMPANY dict (static)
backend/pdf/filters.py                    # Jinja filters (inr_words, format_inr)
backend/pdf/generator.py                  # render_pdf(kind, invoice) -> bytes; render_all_zip
backend/pdf/templates/_base.css           # shared print CSS
backend/pdf/templates/lr.html             # LR template
backend/pdf/templates/party_bill.html     # Party Bill template
backend/pdf/templates/driver_bill.html    # Driver Bill template

tests/test_invoices_db.py                 # DB CRUD + serial allocator tests
tests/test_invoices_api.py                # FastAPI TestClient tests
tests/test_invoices_pdf.py                # PDF smoke tests

frontend/src/pages/InvoicesPage.jsx       # list + KPIs + search
frontend/src/components/InvoiceModal.jsx  # 5-section form
```

**Modified files**

```
backend/requirements.txt                  # add weasyprint, jinja2, num2words
database.py                               # add invoices+invoice_sequences tables + CRUD
backend/api.py                            # add /invoices router (7 endpoints)
frontend/src/api.js                       # add invoice API helpers
frontend/src/App.jsx                      # register /invoices route + modal state
frontend/src/components/Sidebar.jsx       # add "Invoices" nav item (desktop + mobile)
```

---

## Task 1: Add PDF dependencies and scaffold `backend/pdf/`

**Files:**
- Modify: `backend/requirements.txt`
- Create: `backend/__init__.py` (empty — makes `backend` an importable package)
- Create: `backend/pdf/__init__.py`
- Create: `backend/pdf/company.py`
- Test: `tests/test_invoices_pdf.py` (import smoke test)

**Why the `backend/__init__.py`:** Tests need to do `from backend.api import app` and `from backend.pdf.generator import render_pdf`. Without `backend/__init__.py`, Python won't recognize `backend` as a package. The existing `backend/api.py` uses a `sys.path.insert(0, _parent_dir)` hack for its `import database`; keep that hack — we're adding a package init on top of it, not replacing it.

**Interfaces:**
- Consumes: none
- Produces:
  - `backend.pdf.company.COMPANY: dict` — keys: `name, address, jurisdiction, phones (list[str]), gst, logo_path, logo_url`
  - Module import `backend.pdf` resolves without error

- [ ] **Step 1: Add deps to `backend/requirements.txt`**

Append to the file (final content shown, existing lines preserved):

```
fastapi>=0.100.0
uvicorn[standard]>=0.22.0
python-multipart>=0.0.6
openpyxl>=3.1.0
plotly>=5.0.0
weasyprint>=60
jinja2>=3.1
num2words>=0.5.13
```

- [ ] **Step 2: Install deps**

Run: `pip install -r backend/requirements.txt`
Expected: `weasyprint`, `jinja2`, `num2words` install without error. On macOS, WeasyPrint may require `brew install pango gdk-pixbuf libffi` — if `pip install weasyprint` errors with `libpango` missing, run that brew command and retry.

- [ ] **Step 3: Create `backend/__init__.py` and `backend/pdf/__init__.py`**

```bash
touch backend/__init__.py
mkdir -p backend/pdf backend/pdf/templates
touch backend/pdf/__init__.py
```

Both files are intentionally empty — they just mark the packages.

- [ ] **Step 4: Create `backend/pdf/company.py`**

```python
# backend/pdf/company.py
"""Static company info used across all invoice PDF templates."""

from pathlib import Path

_LOGO_ABS = Path(__file__).parent / "assets" / "jb_logo.png"

COMPANY = {
    "name": "JB Transports",
    "address": "201, Shine Swasti, Nr. Godrej Garden City, Gota, Ahmedabad-382470",
    "jurisdiction": "Ahmedabad",
    "phones": ["7600224710"],
    "gst": "24DKCPP6873H2ZS",
    "logo_path": str(_LOGO_ABS),
    "logo_url": _LOGO_ABS.as_uri(),  # file:///... — WeasyPrint reads this from an <img src>
}
```

- [ ] **Step 5: Write the smoke test**

Create `tests/test_invoices_pdf.py`:

```python
def test_pdf_module_imports():
    import backend.pdf                        # noqa: F401
    from backend.pdf.company import COMPANY

    assert COMPANY["name"] == "JB Transports"
    assert isinstance(COMPANY["phones"], list)
    assert len(COMPANY["phones"]) >= 1
    assert "contact_person" not in COMPANY
    assert COMPANY["gst"] == "24DKCPP6873H2ZS"
```

- [ ] **Step 6: Run test**

Run: `pytest tests/test_invoices_pdf.py::test_pdf_module_imports -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/requirements.txt backend/__init__.py backend/pdf/__init__.py backend/pdf/company.py tests/test_invoices_pdf.py
git commit -m "feat(invoices): add PDF dependencies and pdf module skeleton"
```

---

## Task 2: `invoices` and `invoice_sequences` tables + CRUD

**Files:**
- Modify: `database.py`
- Test: `tests/test_invoices_db.py`

**Interfaces:**
- Consumes: existing `database._get_conn()`, `database.init_db()`
- Produces:
  - `database.add_invoice(data: dict) -> tuple[int, str]` — returns `(invoice_id, serial_number)`. Serial allocation is implemented in Task 3; this task stubs it to return `"JB/00-00/000"` and Task 3 replaces the stub.
  - `database.get_all_invoices() -> List[dict]` — newest first
  - `database.get_invoice_by_id(invoice_id: int) -> Optional[dict]`
  - `database.update_invoice(invoice_id: int, data: dict) -> None`
  - `database.delete_invoice(invoice_id: int) -> None`
  - Every returned dict includes all columns + computed fields: `lr_freight_total`, `lr_final_total`, `pb_amount_total`, `db_balance_fare`, `db_expense_total`, `db_savings` (Python-computed inside CRUD, not stored triggers).

- [ ] **Step 1: Write failing test for `add_invoice` + `get_all_invoices`**

Append to `tests/test_invoices_db.py` (create the file):

```python
import pytest
import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.db'))
    database.init_db()


def _minimal():
    return {
        "date": "2026-09-25",
        "vehicle_number": "GJ01AB1234",
        "from_location": "Ahmedabad",
        "to_location": "Sarkhej",
        "consignor_name": "Coal King Biogene Pvt Ltd",
        "consignor_address": "12345 Krishna Complex",
        "consignee_name": "Krishna Traders",
        "consignee_address": "Sanand Road, Ahmedabad",
        "lr_delivery_office_address": "JB Sarkhej Branch",
        "lr_packages": 50,
        "lr_description": "Cotton Bales",
        "lr_weight_nett": 4500.0,
        "lr_weight_charged": 5000.0,
        "lr_rate": 4.8,
        "lr_service_tax": 0.0,
        "lr_st_charge": 0.0,
        "lr_less_advance": 0.0,
        "lr_service_tax_payable_by": "consignor",
        "lr_insurance_risk": "not_insured",
        "lr_insurance_company": "",
        "lr_insurance_policy_no": "",
        "lr_insurance_policy_date": "",
        "lr_insurance_amount": 0.0,
        "lr_ref_invoice_no": "INV-091",
        "lr_ref_value": 250000.0,
        "lr_ref_gst_no": "24AABCC1234X1Z5",
        "pb_bill_to_name": "Coal King Biogene Pvt Ltd",
        "pb_bill_to_address": "12345 Krishna Complex",
        "pb_freight": 24000.0,
        "pb_hamali": 0.0,
        "pb_halting": 0.0,
        "db_driver_name": "Rahish Singh",
        "db_driver_address": "Village Rampur, UP",
        "db_owner_phone": "9935227951",
        "db_transport_party": "Shri Meladi Mata",
        "db_fare": 24000.0,
        "db_advance": 12000.0,
        "db_collection": 0.0,
        "db_previous_balance": 0.0,
        "db_advance_deposited": 0.0,
        "db_expense_office": 670.0,
        "db_expense_collection_ac": 250.0,
        "db_expense_loan": 220.0,
        "db_expense_godown_crane": 0.0,
        "db_expense_st_charge": 50.0,
    }


def test_add_and_list_invoice():
    inv_id, serial = database.add_invoice(_minimal())
    assert inv_id == 1
    assert isinstance(serial, str) and serial  # real format checked in Task 3

    all_ = database.get_all_invoices()
    assert len(all_) == 1
    assert all_[0]["vehicle_number"] == "GJ01AB1234"
    assert all_[0]["serial_number"] == serial
```

- [ ] **Step 2: Run test (should fail)**

Run: `pytest tests/test_invoices_db.py::test_add_and_list_invoice -v`
Expected: FAIL — `AttributeError: module 'database' has no attribute 'add_invoice'`.

- [ ] **Step 3: Extend `database.init_db()` with new tables**

Open `database.py`. Inside `init_db()`, after the existing `trips` migrations block (right before `conn.commit()`), insert:

```python
        # ── invoices ─────────────────────────────────────────────────────
        conn.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT NOT NULL UNIQUE,
                date TEXT NOT NULL,
                vehicle_number TEXT NOT NULL,
                from_location TEXT DEFAULT '',
                to_location TEXT DEFAULT '',
                consignor_name TEXT DEFAULT '',
                consignor_address TEXT DEFAULT '',
                consignee_name TEXT DEFAULT '',
                consignee_address TEXT DEFAULT '',
                lr_delivery_office_address TEXT DEFAULT '',
                lr_packages INTEGER DEFAULT 0,
                lr_description TEXT DEFAULT '',
                lr_weight_nett REAL DEFAULT 0,
                lr_weight_charged REAL DEFAULT 0,
                lr_rate REAL DEFAULT 0,
                lr_service_tax REAL DEFAULT 0,
                lr_st_charge REAL DEFAULT 0,
                lr_less_advance REAL DEFAULT 0,
                lr_service_tax_payable_by TEXT DEFAULT 'consignor',
                lr_insurance_risk TEXT DEFAULT 'not_insured',
                lr_insurance_company TEXT DEFAULT '',
                lr_insurance_policy_no TEXT DEFAULT '',
                lr_insurance_policy_date TEXT DEFAULT '',
                lr_insurance_amount REAL DEFAULT 0,
                lr_ref_invoice_no TEXT DEFAULT '',
                lr_ref_value REAL DEFAULT 0,
                lr_ref_gst_no TEXT DEFAULT '',
                pb_bill_to_name TEXT DEFAULT '',
                pb_bill_to_address TEXT DEFAULT '',
                pb_freight REAL DEFAULT 0,
                pb_hamali REAL DEFAULT 0,
                pb_halting REAL DEFAULT 0,
                db_driver_name TEXT DEFAULT '',
                db_driver_address TEXT DEFAULT '',
                db_owner_phone TEXT DEFAULT '',
                db_transport_party TEXT DEFAULT '',
                db_fare REAL DEFAULT 0,
                db_advance REAL DEFAULT 0,
                db_collection REAL DEFAULT 0,
                db_previous_balance REAL DEFAULT 0,
                db_advance_deposited REAL DEFAULT 0,
                db_expense_office REAL DEFAULT 0,
                db_expense_collection_ac REAL DEFAULT 0,
                db_expense_loan REAL DEFAULT 0,
                db_expense_godown_crane REAL DEFAULT 0,
                db_expense_st_charge REAL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS invoice_sequences (
                financial_year TEXT PRIMARY KEY,
                last_seq INTEGER NOT NULL DEFAULT 0
            )
        ''')
```

- [ ] **Step 4: Add CRUD functions to `database.py`**

Append to `database.py` (at end of file):

```python
# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------
from typing import List, Optional, Tuple  # top-level import if not already present

_INVOICE_COLS = [
    "date", "vehicle_number",
    "from_location", "to_location",
    "consignor_name", "consignor_address",
    "consignee_name", "consignee_address",
    "lr_delivery_office_address", "lr_packages", "lr_description",
    "lr_weight_nett", "lr_weight_charged", "lr_rate",
    "lr_service_tax", "lr_st_charge", "lr_less_advance",
    "lr_service_tax_payable_by",
    "lr_insurance_risk", "lr_insurance_company", "lr_insurance_policy_no",
    "lr_insurance_policy_date", "lr_insurance_amount",
    "lr_ref_invoice_no", "lr_ref_value", "lr_ref_gst_no",
    "pb_bill_to_name", "pb_bill_to_address",
    "pb_freight", "pb_hamali", "pb_halting",
    "db_driver_name", "db_driver_address", "db_owner_phone", "db_transport_party",
    "db_fare", "db_advance", "db_collection",
    "db_previous_balance", "db_advance_deposited",
    "db_expense_office", "db_expense_collection_ac", "db_expense_loan",
    "db_expense_godown_crane", "db_expense_st_charge",
]

_NUMERIC_COLS = {
    "lr_packages",
    "lr_weight_nett", "lr_weight_charged", "lr_rate",
    "lr_service_tax", "lr_st_charge", "lr_less_advance",
    "lr_insurance_amount", "lr_ref_value",
    "pb_freight", "pb_hamali", "pb_halting",
    "db_fare", "db_advance", "db_collection",
    "db_previous_balance", "db_advance_deposited",
    "db_expense_office", "db_expense_collection_ac", "db_expense_loan",
    "db_expense_godown_crane", "db_expense_st_charge",
}


def _enrich_invoice(row: dict) -> dict:
    """Add computed totals to an invoice dict."""
    lr_freight = (row.get("lr_weight_charged") or 0) * (row.get("lr_rate") or 0)
    lr_final = lr_freight + (row.get("lr_service_tax") or 0) + (row.get("lr_st_charge") or 0) - (row.get("lr_less_advance") or 0)
    pb_total = (row.get("pb_freight") or 0) + (row.get("pb_hamali") or 0) + (row.get("pb_halting") or 0)
    db_balance = (row.get("db_fare") or 0) - (row.get("db_advance") or 0)
    db_expense_total = sum([
        row.get("db_expense_office") or 0,
        row.get("db_expense_collection_ac") or 0,
        row.get("db_expense_loan") or 0,
        row.get("db_expense_godown_crane") or 0,
        row.get("db_expense_st_charge") or 0,
    ])
    db_savings = db_balance - db_expense_total
    return {
        **row,
        "lr_freight_total": lr_freight,
        "lr_final_total": lr_final,
        "pb_amount_total": pb_total,
        "db_balance_fare": db_balance,
        "db_expense_total": db_expense_total,
        "db_savings": db_savings,
    }


def _allocate_serial(conn, date_str: str) -> str:
    """STUB — replaced in Task 3 with real FY-scoped allocator."""
    return "JB/00-00/000"


def add_invoice(data: dict) -> Tuple[int, str]:
    now = datetime.now().isoformat()
    values = [data.get(c, "") if c not in _NUMERIC_COLS else (data.get(c) or 0) for c in _INVOICE_COLS]
    with _get_conn() as conn:
        serial = _allocate_serial(conn, data["date"])
        placeholders = ",".join(["?"] * (len(_INVOICE_COLS) + 3))  # +serial,+created,+updated
        cols_sql = ",".join(["serial_number"] + _INVOICE_COLS + ["created_at", "updated_at"])
        cursor = conn.execute(
            f"INSERT INTO invoices ({cols_sql}) VALUES ({placeholders})",
            [serial] + values + [now, now],
        )
        conn.commit()
        return cursor.lastrowid, serial


def get_all_invoices() -> List[dict]:
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM invoices ORDER BY id DESC").fetchall()
        return [_enrich_invoice(dict(r)) for r in rows]


def get_invoice_by_id(invoice_id: int) -> Optional[dict]:
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,)).fetchone()
        return _enrich_invoice(dict(row)) if row else None


def update_invoice(invoice_id: int, data: dict) -> None:
    now = datetime.now().isoformat()
    set_sql = ",".join([f"{c} = ?" for c in _INVOICE_COLS]) + ", updated_at = ?"
    values = [data.get(c, "") if c not in _NUMERIC_COLS else (data.get(c) or 0) for c in _INVOICE_COLS]
    with _get_conn() as conn:
        conn.execute(f"UPDATE invoices SET {set_sql} WHERE id = ?", values + [now, invoice_id])
        conn.commit()


def delete_invoice(invoice_id: int) -> None:
    with _get_conn() as conn:
        conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()
```

- [ ] **Step 5: Run tests**

Run: `pytest tests/test_invoices_db.py::test_add_and_list_invoice -v`
Expected: PASS.

- [ ] **Step 6: Add tests for the other CRUD ops**

Append to `tests/test_invoices_db.py`:

```python
def test_get_invoice_by_id_missing_returns_none():
    assert database.get_invoice_by_id(999) is None


def test_computed_fields_on_read():
    inv_id, _ = database.add_invoice(_minimal())
    row = database.get_invoice_by_id(inv_id)
    assert row["lr_freight_total"] == 5000.0 * 4.8       # 24000
    assert row["lr_final_total"] == 24000.0              # tax=ch=adv=0
    assert row["pb_amount_total"] == 24000.0             # 24000+0+0
    assert row["db_balance_fare"] == 12000.0             # 24000-12000
    assert row["db_expense_total"] == 670 + 250 + 220 + 0 + 50
    assert row["db_savings"] == row["db_balance_fare"] - row["db_expense_total"]


def test_update_invoice_persists_changes():
    inv_id, _ = database.add_invoice(_minimal())
    data = _minimal()
    data["pb_hamali"] = 500.0
    database.update_invoice(inv_id, data)
    row = database.get_invoice_by_id(inv_id)
    assert row["pb_hamali"] == 500.0
    assert row["pb_amount_total"] == 24500.0


def test_delete_invoice_removes_row():
    inv_id, _ = database.add_invoice(_minimal())
    database.delete_invoice(inv_id)
    assert database.get_all_invoices() == []
```

- [ ] **Step 7: Run all invoice DB tests**

Run: `pytest tests/test_invoices_db.py -v`
Expected: all 5 tests PASS.

- [ ] **Step 8: Commit**

```bash
git add database.py tests/test_invoices_db.py
git commit -m "feat(invoices): add invoices tables and CRUD with computed totals"
```

---

## Task 3: FY-scoped atomic serial allocator

**Files:**
- Modify: `database.py` (replace `_allocate_serial` stub, add `preview_next_serial`)
- Test: `tests/test_invoices_db.py` (append tests)

**Interfaces:**
- Consumes: `invoice_sequences` table (Task 2), `_get_conn()`
- Produces:
  - `database._allocate_serial(conn, date_str: str) -> str` — allocates and reserves the next serial for the FY of `date_str`. Called from within a transaction. Format `JB/YY-YY/NNN`.
  - `database.preview_next_serial(date_str: str) -> str` — returns what would be allocated WITHOUT reserving. Called by the frontend for the "will be serial X" hint.
  - `database._financial_year(date_str: str) -> str` — helper returning `"25-26"` for a date in FY 2025-26.

- [ ] **Step 1: Write failing tests for FY math and format**

Append to `tests/test_invoices_db.py`:

```python
def test_financial_year_boundary():
    assert database._financial_year("2026-04-01") == "26-27"
    assert database._financial_year("2026-03-31") == "25-26"
    assert database._financial_year("2026-09-25") == "26-27"
    assert database._financial_year("2026-01-15") == "25-26"


def test_serial_format_and_sequence_within_fy():
    a_id, s1 = database.add_invoice({**_minimal(), "date": "2026-09-25"})
    b_id, s2 = database.add_invoice({**_minimal(), "date": "2026-09-25"})
    assert s1 == "JB/26-27/001"
    assert s2 == "JB/26-27/002"


def test_serial_resets_across_fy():
    _, s_apr = database.add_invoice({**_minimal(), "date": "2026-04-05"})   # FY 26-27
    _, s_mar = database.add_invoice({**_minimal(), "date": "2026-03-30"})   # FY 25-26
    assert s_apr == "JB/26-27/001"
    assert s_mar == "JB/25-26/001"


def test_serial_zero_pads_to_three_then_grows():
    # 1000 iterations would be slow; test the format function directly by
    # driving the sequence table.
    with database._get_conn() as conn:
        conn.execute("INSERT INTO invoice_sequences (financial_year, last_seq) VALUES (?, ?)",
                     ("25-26", 999))
        conn.commit()
    _, s = database.add_invoice({**_minimal(), "date": "2026-03-15"})
    assert s == "JB/25-26/1000"


def test_preview_does_not_reserve():
    p1 = database.preview_next_serial("2026-09-25")
    p2 = database.preview_next_serial("2026-09-25")
    assert p1 == p2 == "JB/26-27/001"
    _, allocated = database.add_invoice({**_minimal(), "date": "2026-09-25"})
    assert allocated == "JB/26-27/001"
    assert database.preview_next_serial("2026-09-25") == "JB/26-27/002"
```

- [ ] **Step 2: Run tests (should fail)**

Run: `pytest tests/test_invoices_db.py -v -k "financial_year or serial or preview"`
Expected: FAIL — `AttributeError: module 'database' has no attribute '_financial_year'` (and the serial format tests fail because the stub returns `"JB/00-00/000"`).

- [ ] **Step 3: Replace the stub in `database.py`**

Replace the `_allocate_serial` stub with the real implementation, and add helpers:

```python
def _financial_year(date_str: str) -> str:
    """Return 'YY-YY' financial-year label for date_str (YYYY-MM-DD).
    FY runs Apr 1 -> Mar 31."""
    from datetime import date as _date
    y, m, d = [int(p) for p in date_str.split("-")]
    if m >= 4:
        start = y
    else:
        start = y - 1
    return f"{start % 100:02d}-{(start + 1) % 100:02d}"


def _allocate_serial(conn, date_str: str) -> str:
    fy = _financial_year(date_str)
    # Upsert + read in same transaction. sqlite3 module opens BEGIN implicitly.
    conn.execute(
        "INSERT INTO invoice_sequences (financial_year, last_seq) VALUES (?, 0) "
        "ON CONFLICT(financial_year) DO NOTHING",
        (fy,),
    )
    conn.execute(
        "UPDATE invoice_sequences SET last_seq = last_seq + 1 WHERE financial_year = ?",
        (fy,),
    )
    row = conn.execute(
        "SELECT last_seq FROM invoice_sequences WHERE financial_year = ?",
        (fy,),
    ).fetchone()
    seq = row[0]
    return f"JB/{fy}/{seq:03d}"


def preview_next_serial(date_str: str) -> str:
    """Peek what the NEXT allocation for date_str would be, without reserving."""
    fy = _financial_year(date_str)
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT last_seq FROM invoice_sequences WHERE financial_year = ?",
            (fy,),
        ).fetchone()
        next_seq = (row[0] if row else 0) + 1
    return f"JB/{fy}/{next_seq:03d}"
```

- [ ] **Step 4: Run all Task 3 tests**

Run: `pytest tests/test_invoices_db.py -v`
Expected: all tests PASS (Task 2 + Task 3 tests).

- [ ] **Step 5: Commit**

```bash
git add database.py tests/test_invoices_db.py
git commit -m "feat(invoices): FY-scoped atomic serial allocator + preview"
```

---

## Task 4: PDF rendering engine (Jinja + WeasyPrint wrapper + base CSS)

**Files:**
- Create: `backend/pdf/filters.py`
- Create: `backend/pdf/generator.py`
- Create: `backend/pdf/templates/_base.css`
- Test: `tests/test_invoices_pdf.py` (append)

**Interfaces:**
- Consumes: `backend.pdf.company.COMPANY`, `database.get_invoice_by_id`
- Produces:
  - `backend.pdf.generator.render_pdf(kind: str, invoice: dict) -> bytes` — `kind` in `{"lr","party_bill","driver_bill"}`. Returns PDF bytes.
  - `backend.pdf.generator.render_all_zip(invoice: dict) -> bytes` — Zip archive containing `lr.pdf`, `party_bill.pdf`, `driver_bill.pdf`.
  - Jinja filter `inr_words(n) -> str` (registered in the env)
  - Jinja filter `format_inr(n) -> str` (e.g., `24000 -> "24,000"`)

- [ ] **Step 1: Write filters**

Create `backend/pdf/filters.py`:

```python
"""Custom Jinja filters used across invoice templates."""
from num2words import num2words


def inr_words(n) -> str:
    """Convert a rupee amount to Indian-style words (Lakh/Crore)."""
    if n is None:
        return ""
    rupees = int(round(float(n)))
    words = num2words(rupees, lang="en_IN")
    # num2words returns lowercase and hyphenated; title-case for bills.
    return f"Rupees {words.title()} Only"


def format_inr(n) -> str:
    """Format a number in Indian grouping: 100000 -> '1,00,000'."""
    if n is None or n == "":
        return ""
    try:
        num = float(n)
    except (TypeError, ValueError):
        return str(n)
    if num == 0:
        return "0"
    # Handle negatives and decimals separately.
    negative = num < 0
    num = abs(num)
    integer, dot, decimal = f"{num:.2f}".partition(".")
    # Trim trailing zeros in decimal but keep at least none.
    decimal = decimal.rstrip("0")
    # Indian grouping: last 3 digits, then groups of 2.
    if len(integer) <= 3:
        grouped = integer
    else:
        grouped = integer[-3:]
        rest = integer[:-3]
        while len(rest) > 2:
            grouped = rest[-2:] + "," + grouped
            rest = rest[:-2]
        grouped = rest + "," + grouped
    out = grouped + ("." + decimal if decimal else "")
    return ("-" if negative else "") + out
```

- [ ] **Step 2: Write base CSS**

Create `backend/pdf/templates/_base.css`:

```css
@page {
  size: A4;
  margin: 12mm 14mm;
}

body {
  font-family: 'Times New Roman', Times, serif;
  font-size: 11pt;
  color: #111;
  margin: 0;
}

table { border-collapse: collapse; width: 100%; }
.hair td, .hair th { border: 1px solid #111; padding: 4px 6px; }
.hair th { background: #f2f2f2; font-weight: 600; }

.qr-slot {
  width: 22mm; height: 22mm;
  border: 1px dashed #888;
  display: flex; align-items: center; justify-content: center;
  font-size: 8pt; color: #888;
}

.right { text-align: right; }
.center { text-align: center; }
.bold { font-weight: bold; }
.small { font-size: 9pt; }
```

- [ ] **Step 3: Write the generator**

Create `backend/pdf/generator.py`:

```python
"""Render invoice PDFs from HTML templates via WeasyPrint."""
import io
import zipfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS

from backend.pdf.company import COMPANY
from backend.pdf.filters import inr_words, format_inr

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)
_env.filters["inr_words"] = inr_words
_env.filters["format_inr"] = format_inr

_KIND_TO_TEMPLATE = {
    "lr": "lr.html",
    "party_bill": "party_bill.html",
    "driver_bill": "driver_bill.html",
}


def render_pdf(kind: str, invoice: dict) -> bytes:
    template_name = _KIND_TO_TEMPLATE.get(kind)
    if not template_name:
        raise ValueError(f"unknown kind: {kind!r}")
    template = _env.get_template(template_name)
    html = template.render(inv=invoice, company=COMPANY)
    base_css = CSS(filename=str(_TEMPLATES_DIR / "_base.css"))
    return HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf(stylesheets=[base_css])


def render_all_zip(invoice: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for kind in ("lr", "party_bill", "driver_bill"):
            z.writestr(f"{invoice['serial_number'].replace('/', '_')}_{kind}.pdf",
                       render_pdf(kind, invoice))
    return buf.getvalue()
```

- [ ] **Step 4: Create empty template placeholders (real templates land in Tasks 5-7)**

Create three minimal HTML files so `render_pdf` doesn't crash before Tasks 5-7 flesh them out:

`backend/pdf/templates/lr.html`:
```html
<!doctype html><html><body><h1>LR {{ inv.serial_number }}</h1></body></html>
```

`backend/pdf/templates/party_bill.html`:
```html
<!doctype html><html><body><h1>Party Bill {{ inv.serial_number }}</h1></body></html>
```

`backend/pdf/templates/driver_bill.html`:
```html
<!doctype html><html><body><h1>Driver Bill {{ inv.serial_number }}</h1></body></html>
```

- [ ] **Step 5: Write generator tests**

Append to `tests/test_invoices_pdf.py`:

```python
import pytest
import database
from backend.pdf.generator import render_pdf, render_all_zip
from backend.pdf.filters import inr_words, format_inr


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.db'))
    database.init_db()


def _seed_invoice():
    # Import here so this file remains valid even if test_invoices_db.py moves.
    from tests.test_invoices_db import _minimal
    inv_id, _ = database.add_invoice(_minimal())
    return database.get_invoice_by_id(inv_id)


def test_format_inr_indian_grouping():
    assert format_inr(0) == "0"
    assert format_inr(1000) == "1,000"
    assert format_inr(100000) == "1,00,000"
    assert format_inr(12345678) == "1,23,45,678"
    assert format_inr(1234.5) == "1,234.5"


def test_inr_words_smoke():
    assert "Twenty Four Thousand" in inr_words(24000)


@pytest.mark.parametrize("kind", ["lr", "party_bill", "driver_bill"])
def test_render_pdf_kind_produces_pdf_bytes(kind):
    inv = _seed_invoice()
    pdf = render_pdf(kind, inv)
    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1000  # non-trivial size


def test_render_all_zip_contains_three_pdfs():
    inv = _seed_invoice()
    blob = render_all_zip(inv)
    import io, zipfile
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        names = z.namelist()
    assert len(names) == 3
    assert any(n.endswith("_lr.pdf") for n in names)
    assert any(n.endswith("_party_bill.pdf") for n in names)
    assert any(n.endswith("_driver_bill.pdf") for n in names)
```

- [ ] **Step 6: Run tests**

Run: `pytest tests/test_invoices_pdf.py -v`
Expected: all tests PASS.

- [ ] **Step 7: Commit**

```bash
git add backend/pdf/filters.py backend/pdf/generator.py backend/pdf/templates/_base.css backend/pdf/templates/lr.html backend/pdf/templates/party_bill.html backend/pdf/templates/driver_bill.html tests/test_invoices_pdf.py
git commit -m "feat(invoices): PDF rendering engine with Jinja + WeasyPrint + INR filters"
```

---

## Task 5: LR PDF template (full layout)

**Files:**
- Modify: `backend/pdf/templates/lr.html`
- Test: `tests/test_invoices_pdf.py` (append content assertions)

**Interfaces:**
- Consumes: `inv` (invoice dict from `database.get_invoice_by_id`), `company` (COMPANY dict from Task 1)
- Produces: PDF whose text content includes serial, vehicle number, both party names/addresses, freight total, service-tax-payable-by selection, insurance risk selection, reference invoice number

- [ ] **Step 1: Replace `backend/pdf/templates/lr.html` with the full layout**

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>LR {{ inv.serial_number }}</title></head>
<body>

<div class="center small">Subject To {{ company.jurisdiction }} Jurisdiction Only</div>

<table style="margin-bottom:6px;">
  <tr>
    <td style="width:60%;vertical-align:middle;">
      <img src="{{ company.logo_url }}" style="height:28mm;width:auto;" alt="{{ company.name }}" />
    </td>
    <td class="right small" style="vertical-align:top;">
      <div>{{ company.phones | join(', ') }}</div>
      <div style="margin-top:4px;display:flex;justify-content:flex-end;"><div class="qr-slot">QR</div></div>
    </td>
  </tr>
</table>

<table class="hair small" style="margin-bottom:6px;">
  <tr>
    <td style="width:25%;vertical-align:top;">
      <div class="bold">CAUTION</div>
      <div>The consignment will not be detained, diverted, re-routed without consignee Bank's written permission. Will be delivered at destination.</div>
    </td>
    <td style="width:25%;vertical-align:top;">
      <div class="center bold">AT OWNER'S RISK</div>
      <div class="bold">INSURANCE</div>
      <div>The consignor has stated that:</div>
      <div>{{ '☑' if inv.lr_insurance_risk == 'not_insured' else '☐' }} He has not insured that consignment</div>
      <div>{{ '☑' if inv.lr_insurance_risk == 'insured' else '☐' }} He has insured the consignment</div>
      <div>Company: {{ inv.lr_insurance_company or '________' }}</div>
      <div>Policy No: {{ inv.lr_insurance_policy_no or '________' }} &nbsp; Date: {{ inv.lr_insurance_policy_date or '________' }}</div>
      <div>Amount: {{ inv.lr_insurance_amount | format_inr }} &nbsp; Risk: {{ inv.lr_insurance_risk | replace('_',' ') | title }}</div>
    </td>
    <td style="width:25%;vertical-align:top;">
      <div class="bold">SCHEDULE OF DEMURRAGE CHARGES</div>
      <div>Demurrage is chargable after ___ days from today @ Rs. ___ per day per Qtl on Weight Charged.</div>
    </td>
    <td style="width:25%;vertical-align:top;">
      <div>Truck No.: <span class="bold">{{ inv.vehicle_number }}</span></div>
      <div class="center bold" style="margin-top:4px;">NOTICE</div>
      <div style="font-size:8pt;">The Consignment covered by this Lorry Receipt shall be stored at destination under the control of the Transport Operator and shall be delivered to or to the order of the Consignee Bank whose name is mentioned in the Lorry Receipt.</div>
    </td>
  </tr>
</table>

<table class="hair" style="margin-bottom:6px;">
  <tr>
    <td style="width:33%;vertical-align:top;">
      <div class="center bold">CONSIGNMENT NOTE</div>
      <div class="center" style="font-size:18pt;font-weight:bold;">{{ inv.serial_number }}</div>
    </td>
    <td style="width:67%;vertical-align:top;">
      <div>Address Of Delivery Office:</div>
      <div class="bold">{{ inv.lr_delivery_office_address }}</div>
    </td>
  </tr>
</table>

<table class="hair" style="margin-bottom:6px;">
  <tr>
    <td style="width:60%;vertical-align:top;">
      <div><span class="bold">CONSIGNOR'S:</span> {{ inv.consignor_name }}</div>
      <div style="margin-left:70px;">{{ inv.consignor_address }}</div>
      <div style="margin-top:6px;"><span class="bold">CONSIGNEE'S:</span> {{ inv.consignee_name }}</div>
      <div style="margin-left:70px;">{{ inv.consignee_address }}</div>
    </td>
    <td style="width:40%;vertical-align:top;">
      <div>Date: <span class="bold">{{ inv.date }}</span></div>
      <div>From: <span class="bold">{{ inv.from_location }}</span></div>
      <div>To: <span class="bold">{{ inv.to_location }}</span></div>
    </td>
  </tr>
</table>

<table class="hair" style="margin-bottom:6px;">
  <thead>
    <tr>
      <th>Packages</th>
      <th>Description ( Said to Contain )</th>
      <th>Weight Nett</th>
      <th>Weight Charged</th>
      <th>Rate</th>
      <th colspan="2">FREIGHT ACCOUNT PAY / PAID</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="center">{{ inv.lr_packages }}</td>
      <td>{{ inv.lr_description }}</td>
      <td class="center">{{ inv.lr_weight_nett | format_inr }}</td>
      <td class="center">{{ inv.lr_weight_charged | format_inr }}</td>
      <td class="right">{{ inv.lr_rate }}</td>
      <td class="right">{{ inv.lr_freight_total | format_inr }}</td>
      <td class="right">00</td>
    </tr>
    <tr>
      <td colspan="5" style="vertical-align:top;height:80pt;">
        <div style="margin-top:4px;"><span class="bold">Service Tax Payable By:</span></div>
        <div>
          {{ '☑' if inv.lr_service_tax_payable_by == 'consignor' else '☐' }} Consignor
          &nbsp;&nbsp; {{ '☑' if inv.lr_service_tax_payable_by == 'consignee' else '☐' }} Consignee
          &nbsp;&nbsp; {{ '☑' if inv.lr_service_tax_payable_by == 'transporter' else '☐' }} Transporter
        </div>
        <div style="margin-top:12pt;font-style:italic;">Not responsible for any Breakage, Leakage, Damage, Bulates goods &amp; Fires</div>
      </td>
      <td colspan="2" style="padding:0;">
        <table style="width:100%;font-size:11pt;">
          <tr><td class="right" style="padding-right:4px;border-bottom:1px solid #111;">S. Tax</td><td class="right" style="padding-right:4px;border-bottom:1px solid #111;border-left:1px solid #111;">{{ inv.lr_service_tax | format_inr }}</td></tr>
          <tr><td class="right" style="padding-right:4px;border-bottom:1px solid #111;">St. Ch</td><td class="right" style="padding-right:4px;border-bottom:1px solid #111;border-left:1px solid #111;">{{ inv.lr_st_charge | format_inr }}</td></tr>
          <tr><td class="right" style="padding-right:4px;border-bottom:1px solid #111;">Total</td><td class="right" style="padding-right:4px;border-bottom:1px solid #111;border-left:1px solid #111;">{{ inv.lr_freight_total | format_inr }}</td></tr>
          <tr><td class="right" style="padding-right:4px;border-bottom:1px solid #111;">Less Adv.</td><td class="right" style="padding-right:4px;border-bottom:1px solid #111;border-left:1px solid #111;">{{ inv.lr_less_advance | format_inr }}</td></tr>
          <tr><td class="right bold" style="padding-right:4px;">Total</td><td class="right bold" style="padding-right:4px;border-left:1px solid #111;">{{ inv.lr_final_total | format_inr }}</td></tr>
        </table>
      </td>
    </tr>
  </tbody>
</table>

<table style="margin-top:12pt;">
  <tr>
    <td style="width:60%;vertical-align:bottom;">
      <div>Invoice No: <span class="bold">{{ inv.lr_ref_invoice_no }}</span></div>
      <div>Value: <span class="bold">{{ inv.lr_ref_value | format_inr }}</span> &nbsp;&nbsp; G.S.T No: <span class="bold">{{ inv.lr_ref_gst_no }}</span></div>
    </td>
    <td style="width:40%;text-align:right;vertical-align:bottom;">
      <div class="bold">For, {{ company.name }}</div>
      <div style="margin-top:24pt;border-top:1px solid #111;padding-top:2pt;">Signature</div>
    </td>
  </tr>
</table>

</body></html>
```

- [ ] **Step 2: Add content-assertion tests**

Append to `tests/test_invoices_pdf.py`:

```python
def _pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF for content checks. Uses pdfminer via WeasyPrint's dep tree."""
    from pdfminer.high_level import extract_text
    import io
    return extract_text(io.BytesIO(pdf_bytes))


def test_lr_pdf_contains_key_fields():
    inv = _seed_invoice()
    text = _pdf_text(render_pdf("lr", inv))
    assert inv["serial_number"] in text
    assert inv["vehicle_number"] in text
    assert "Coal King Biogene" in text
    assert "Krishna Traders" in text
    assert "24,000" in text  # freight total
    assert "Ahmedabad Jurisdiction" in text
```

Note: `pdfminer.six` ships with WeasyPrint's dependency tree; if `import pdfminer.high_level` fails, run `pip install pdfminer.six` and add it to `backend/requirements.txt`.

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_invoices_pdf.py -v`
Expected: all PDF tests PASS, including the new LR content check.

- [ ] **Step 4: Manual eyeball**

Run once from a Python REPL:
```python
from tests.test_invoices_db import _minimal
import database; database.init_db()
inv_id, _ = database.add_invoice(_minimal())
inv = database.get_invoice_by_id(inv_id)
from backend.pdf.generator import render_pdf
open("/tmp/lr.pdf","wb").write(render_pdf("lr", inv))
```
Then `open /tmp/lr.pdf`. Confirm layout roughly matches `docs/superpowers/mockups/invoices-mockup.html` (PDF: LR tab).

- [ ] **Step 5: Commit**

```bash
git add backend/pdf/templates/lr.html tests/test_invoices_pdf.py
git commit -m "feat(invoices): full LR PDF template with content assertion tests"
```

---

## Task 6: Party Bill PDF template

**Files:**
- Modify: `backend/pdf/templates/party_bill.html`
- Test: `tests/test_invoices_pdf.py` (append)

**Interfaces:** Same as Task 5.

- [ ] **Step 1: Replace `backend/pdf/templates/party_bill.html`**

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>Party Bill {{ inv.serial_number }}</title></head>
<body>

<div class="center small">Subject to {{ company.jurisdiction }} Jurisdiction</div>

<table style="margin-bottom:4px;">
  <tr>
    <td style="width:60%;vertical-align:middle;">
      <img src="{{ company.logo_url }}" style="height:28mm;width:auto;" alt="{{ company.name }}" />
    </td>
    <td class="right small" style="vertical-align:top;">
      <div>Mobile: {{ company.phones[0] }}</div>
      <div style="margin-top:4px;display:flex;justify-content:flex-end;"><div class="qr-slot">QR</div></div>
    </td>
  </tr>
</table>

<table class="hair" style="margin-bottom:4px;">
  <tr>
    <td>Bill No: <span class="bold">{{ inv.serial_number }}</span></td>
    <td>Date: <span class="bold">{{ inv.date }}</span></td>
  </tr>
  <tr>
    <td colspan="2">
      To M/s: <span class="bold">{{ inv.pb_bill_to_name }}</span><br/>
      Off: <span class="bold">{{ inv.pb_bill_to_address }}</span>
    </td>
  </tr>
</table>

<table class="hair">
  <thead>
    <tr>
      <th>Billty No</th>
      <th>Date</th>
      <th>Particulars</th>
      <th>Freight</th>
      <th>Hamali</th>
      <th>Halting</th>
      <th colspan="2">Amount<br/><span class="small">Rs. &nbsp; Ps.</span></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="center">{{ inv.serial_number }}</td>
      <td class="center">{{ inv.date }}</td>
      <td>
        Invoice No: {{ inv.lr_ref_invoice_no }}<br/>
        Date: {{ inv.date }}<br/><br/>
        We hereby Submit our bill for transportation of your goods.<br/><br/>
        Vehicle: {{ inv.vehicle_number }}
      </td>
      <td class="right">{{ inv.pb_freight | format_inr }}</td>
      <td class="right">{{ inv.pb_hamali | format_inr if inv.pb_hamali else '—' }}</td>
      <td class="right">{{ inv.pb_halting | format_inr if inv.pb_halting else '—' }}</td>
      <td class="right">{{ inv.pb_amount_total | format_inr }}</td>
      <td class="right">00</td>
    </tr>
    <tr style="height:40pt;"><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
    <tr style="height:40pt;"><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
  </tbody>
</table>

<table style="margin-top:6pt;">
  <tr>
    <td style="width:50%;vertical-align:top;border:1px solid #111;padding:6pt;">
      <div>GST No: <span class="bold">{{ company.gst }}</span></div>
      <div style="margin-top:6pt;">Rs. (in words): <span style="font-style:italic;font-weight:bold;">{{ inv.pb_amount_total | inr_words }}</span></div>
      <div style="margin-top:6pt;" class="small">After 30 days interest @ 18% annual will be on out standing bills.</div>
      <div style="margin-top:12pt;">Checked By: ____________________</div>
    </td>
    <td style="width:50%;vertical-align:top;border:1px solid #111;padding:6pt;">
      <div style="display:flex;justify-content:space-between;font-weight:bold;"><span>Total Rs.</span><span>{{ inv.pb_amount_total | format_inr }}</span></div>
      <div class="right" style="margin-top:40pt;border-top:1px solid #111;padding-top:2pt;">For, {{ company.name }}</div>
    </td>
  </tr>
</table>

</body></html>
```

- [ ] **Step 2: Add content-assertion test**

Append to `tests/test_invoices_pdf.py`:

```python
def test_party_bill_pdf_contains_key_fields():
    inv = _seed_invoice()
    text = _pdf_text(render_pdf("party_bill", inv))
    assert inv["serial_number"] in text
    assert "Coal King Biogene" in text
    assert "24,000" in text                  # total
    assert "Twenty Four Thousand" in text    # amount in words
    assert "24DKCPP6873H2ZS" in text         # GST from company
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_invoices_pdf.py -v`
Expected: PASS.

- [ ] **Step 4: Manual eyeball**

Repeat the REPL check from Task 5 with `render_pdf("party_bill", inv)` → open `/tmp/pb.pdf`.

- [ ] **Step 5: Commit**

```bash
git add backend/pdf/templates/party_bill.html tests/test_invoices_pdf.py
git commit -m "feat(invoices): full Party Bill PDF template"
```

---

## Task 7: Driver Bill PDF template

**Files:**
- Modify: `backend/pdf/templates/driver_bill.html`
- Test: `tests/test_invoices_pdf.py` (append)

**Interfaces:** Same as Task 5.

- [ ] **Step 1: Replace `backend/pdf/templates/driver_bill.html`**

```html
<!doctype html>
<html><head><meta charset="utf-8"><title>Driver Bill {{ inv.serial_number }}</title></head>
<body>

<table style="margin-bottom:4px;">
  <tr>
    <td style="width:60%;vertical-align:middle;">
      <img src="{{ company.logo_url }}" style="height:28mm;width:auto;" alt="{{ company.name }}" />
    </td>
    <td class="right small" style="vertical-align:top;">
      <div>M: {{ company.phones[0] }}</div>
      <div style="margin-top:4px;display:flex;justify-content:flex-end;"><div class="qr-slot">QR</div></div>
    </td>
  </tr>
</table>

<div class="center bold" style="border-top:1px solid #111;border-bottom:1px solid #111;padding:2pt 0;margin-bottom:6pt;font-size:14pt;">DRIVER BILL</div>

<table class="hair" style="margin-bottom:4px;">
  <tr>
    <td>No./AMD/ <span class="bold">{{ inv.serial_number }}</span></td>
    <td>Date: <span class="bold">{{ inv.date }}</span></td>
  </tr>
</table>

<table style="margin-bottom:4px;">
  <tr>
    <td style="width:60%;border:1px solid #111;padding:6pt;vertical-align:top;">
      <div>Truck No: <span class="bold">{{ inv.vehicle_number }}</span></div>
      <div>Driver / Owner Name: <span class="bold">{{ inv.db_driver_name }}</span></div>
      <div>Address: <span class="bold">{{ inv.db_driver_address }}</span></div>
      <div>Phone (Owner): <span class="bold">{{ inv.db_owner_phone }}</span></div>
      <div>Transport Party: <span class="bold">{{ inv.db_transport_party }}</span></div>
    </td>
    <td style="width:40%;border:1px solid #111;padding:6pt;vertical-align:top;">
      <div style="display:flex;justify-content:space-between;"><span>Total Advance:</span><span class="bold">{{ inv.db_advance | format_inr }}</span></div>
      <div style="display:flex;justify-content:space-between;"><span>Previous Balance:</span><span class="bold">{{ inv.db_previous_balance | format_inr if inv.db_previous_balance else '—' }}</span></div>
      <div style="display:flex;justify-content:space-between;"><span>Advance Total:</span><span class="bold">{{ inv.db_advance | format_inr }}</span></div>
      <div style="display:flex;justify-content:space-between;"><span>Total Expense:</span><span class="bold">{{ inv.db_expense_total | format_inr }}</span></div>
      <div style="display:flex;justify-content:space-between;" class="bold"><span>Savings:</span><span>{{ inv.db_savings | format_inr }}</span></div>
      <div style="display:flex;justify-content:space-between;"><span>Advance Deposited:</span><span>{{ inv.db_advance_deposited | format_inr if inv.db_advance_deposited else '—' }}</span></div>
    </td>
  </tr>
</table>

<table class="hair" style="margin-bottom:4px;">
  <thead>
    <tr>
      <th>Fare</th><th>Advance</th><th>Balance Fare</th><th>Collection</th>
      <th>Office Expense</th><th>Amount</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="right">{{ inv.db_fare | format_inr }}</td>
      <td class="right">{{ inv.db_advance | format_inr }}</td>
      <td class="right">{{ inv.db_balance_fare | format_inr }}</td>
      <td class="right">{{ inv.db_collection | format_inr if inv.db_collection else '—' }}</td>
      <td>Office Expense</td>
      <td class="right">{{ inv.db_expense_office | format_inr }}</td>
    </tr>
    <tr><td></td><td></td><td></td><td></td><td>Collection A/C</td><td class="right">{{ inv.db_expense_collection_ac | format_inr }}</td></tr>
    <tr><td></td><td></td><td></td><td></td><td>Loan</td><td class="right">{{ inv.db_expense_loan | format_inr }}</td></tr>
    <tr><td></td><td></td><td></td><td></td><td>Godown Crane</td><td class="right">{{ inv.db_expense_godown_crane | format_inr if inv.db_expense_godown_crane else '—' }}</td></tr>
    <tr><td></td><td></td><td></td><td></td><td>Dala / Munshiyana / ST Charge</td><td class="right">{{ inv.db_expense_st_charge | format_inr }}</td></tr>
    <tr class="bold">
      <td class="right">{{ inv.db_fare | format_inr }}</td>
      <td class="right">{{ inv.db_advance | format_inr }}</td>
      <td class="right">{{ inv.db_balance_fare | format_inr }}</td>
      <td class="right">{{ inv.db_collection | format_inr if inv.db_collection else '—' }}</td>
      <td class="right">Total</td>
      <td class="right">{{ inv.db_expense_total | format_inr }}</td>
    </tr>
  </tbody>
</table>

<div class="small" style="margin-bottom:12pt;">
  <div class="bold">Notes:</div>
  <div>1) If the vehicle is delayed, inform the party immediately.</div>
  <div>2) Responsibility for delay lies with the vehicle owner / driver.</div>
  <div>3) If return fare is not received within 15 days, balance fare will not be paid.</div>
</div>

<table style="margin-top:20pt;">
  <tr>
    <td class="center"><div style="border-top:1px solid #111;padding-top:2pt;width:180pt;">Driver's Signature</div></td>
    <td class="center right"><div style="border-top:1px solid #111;padding-top:2pt;width:180pt;margin-left:auto;">Partner</div></td>
  </tr>
</table>

</body></html>
```

- [ ] **Step 2: Add content-assertion test**

Append to `tests/test_invoices_pdf.py`:

```python
def test_driver_bill_pdf_contains_key_fields():
    inv = _seed_invoice()
    text = _pdf_text(render_pdf("driver_bill", inv))
    assert inv["serial_number"] in text
    assert "Rahish Singh" in text
    assert "Shri Meladi Mata" in text
    assert "12,000" in text            # balance_fare
    assert "Driver's Signature" in text
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_invoices_pdf.py -v`
Expected: PASS.

- [ ] **Step 4: Manual eyeball**

Repeat the REPL check with `render_pdf("driver_bill", inv)` → `/tmp/db.pdf`.

- [ ] **Step 5: Commit**

```bash
git add backend/pdf/templates/driver_bill.html tests/test_invoices_pdf.py
git commit -m "feat(invoices): full Driver Bill PDF template"
```

---

## Task 8: Backend REST API + PDF endpoints

**Files:**
- Modify: `backend/api.py`
- Test: `tests/test_invoices_api.py`

**Interfaces:**
- Consumes: `database.add_invoice / get_all_invoices / get_invoice_by_id / update_invoice / delete_invoice / preview_next_serial`, `backend.pdf.generator.render_pdf / render_all_zip`
- Produces (JSON via HTTP):
  - `GET  /invoices` → `list[InvoiceOut]`
  - `POST /invoices` → `{"id": int, "serial_number": str}`, 201
  - `GET  /invoices/{id}` → `InvoiceOut`
  - `PUT  /invoices/{id}` → `InvoiceOut`
  - `DELETE /invoices/{id}` → 204
  - `GET  /invoices/{id}/pdf/{kind}` → `application/pdf`
  - `GET  /invoices/{id}/pdf/all` → `application/zip`
  - `GET  /invoices/next-serial?date=YYYY-MM-DD` → `{"serial": str}`

- [ ] **Step 1: Write failing API tests**

Create `tests/test_invoices_api.py`:

```python
import pytest
from fastapi.testclient import TestClient

import database
from backend.api import app


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.db'))
    database.init_db()


@pytest.fixture
def client():
    return TestClient(app)


def _payload():
    from tests.test_invoices_db import _minimal
    return _minimal()


def test_next_serial_endpoint(client):
    r = client.get("/invoices/next-serial", params={"date": "2026-09-25"})
    assert r.status_code == 200
    assert r.json() == {"serial": "JB/26-27/001"}


def test_create_and_list(client):
    r = client.post("/invoices", json=_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["serial_number"] == "JB/26-27/001"

    r = client.get("/invoices")
    assert r.status_code == 200
    invoices = r.json()
    assert len(invoices) == 1
    assert invoices[0]["serial_number"] == "JB/26-27/001"
    assert invoices[0]["lr_freight_total"] == 24000.0  # enrichment


def test_get_update_delete(client):
    r = client.post("/invoices", json=_payload())
    inv_id = r.json()["id"]

    r = client.get(f"/invoices/{inv_id}")
    assert r.status_code == 200
    assert r.json()["vehicle_number"] == "GJ01AB1234"

    updated = _payload()
    updated["pb_hamali"] = 500.0
    r = client.put(f"/invoices/{inv_id}", json=updated)
    assert r.status_code == 200
    assert r.json()["pb_amount_total"] == 24500.0

    r = client.delete(f"/invoices/{inv_id}")
    assert r.status_code == 204
    assert client.get("/invoices").json() == []


def test_get_missing_returns_404(client):
    r = client.get("/invoices/999")
    assert r.status_code == 404


@pytest.mark.parametrize("kind", ["lr", "party_bill", "driver_bill"])
def test_pdf_endpoint_returns_pdf(client, kind):
    r = client.post("/invoices", json=_payload())
    inv_id = r.json()["id"]
    r = client.get(f"/invoices/{inv_id}/pdf/{kind}")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF-")


def test_pdf_endpoint_unknown_kind_returns_400(client):
    r = client.post("/invoices", json=_payload())
    inv_id = r.json()["id"]
    r = client.get(f"/invoices/{inv_id}/pdf/wat")
    assert r.status_code == 400


def test_pdf_all_returns_zip(client):
    r = client.post("/invoices", json=_payload())
    inv_id = r.json()["id"]
    r = client.get(f"/invoices/{inv_id}/pdf/all")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert r.content[:2] == b"PK"  # zip magic
```

- [ ] **Step 2: Run tests (should fail)**

Run: `pytest tests/test_invoices_api.py -v`
Expected: FAIL — 404 on all `/invoices` routes (endpoints not defined yet).

- [ ] **Step 3: Add the invoice router to `backend/api.py`**

Append to `backend/api.py`:

```python
# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------
from typing import Optional  # already imported at top; harmless if duplicated
from fastapi import Query
from fastapi.responses import Response
from backend.pdf.generator import render_pdf, render_all_zip


class InvoiceIn(BaseModel):
    date: str
    vehicle_number: str
    from_location: str = ""
    to_location: str = ""
    consignor_name: str = ""
    consignor_address: str = ""
    consignee_name: str = ""
    consignee_address: str = ""
    lr_delivery_office_address: str = ""
    lr_packages: int = 0
    lr_description: str = ""
    lr_weight_nett: float = 0.0
    lr_weight_charged: float = 0.0
    lr_rate: float = 0.0
    lr_service_tax: float = 0.0
    lr_st_charge: float = 0.0
    lr_less_advance: float = 0.0
    lr_service_tax_payable_by: str = "consignor"
    lr_insurance_risk: str = "not_insured"
    lr_insurance_company: str = ""
    lr_insurance_policy_no: str = ""
    lr_insurance_policy_date: str = ""
    lr_insurance_amount: float = 0.0
    lr_ref_invoice_no: str = ""
    lr_ref_value: float = 0.0
    lr_ref_gst_no: str = ""
    pb_bill_to_name: str = ""
    pb_bill_to_address: str = ""
    pb_freight: float = 0.0
    pb_hamali: float = 0.0
    pb_halting: float = 0.0
    db_driver_name: str = ""
    db_driver_address: str = ""
    db_owner_phone: str = ""
    db_transport_party: str = ""
    db_fare: float = 0.0
    db_advance: float = 0.0
    db_collection: float = 0.0
    db_previous_balance: float = 0.0
    db_advance_deposited: float = 0.0
    db_expense_office: float = 0.0
    db_expense_collection_ac: float = 0.0
    db_expense_loan: float = 0.0
    db_expense_godown_crane: float = 0.0
    db_expense_st_charge: float = 0.0


def _invoice_or_404(inv_id: int) -> dict:
    inv = database.get_invoice_by_id(inv_id)
    if inv is None:
        raise HTTPException(404, f"Invoice {inv_id} not found")
    return inv


@app.get("/invoices/next-serial")
def next_serial(date: str = Query(...)):
    return {"serial": database.preview_next_serial(date)}


@app.get("/invoices")
def list_invoices():
    return database.get_all_invoices()


@app.post("/invoices", status_code=201)
def create_invoice(body: InvoiceIn):
    inv_id, serial = database.add_invoice(body.dict())
    return {"id": inv_id, "serial_number": serial}


@app.get("/invoices/{inv_id}")
def get_invoice(inv_id: int):
    return _invoice_or_404(inv_id)


@app.put("/invoices/{inv_id}")
def update_invoice(inv_id: int, body: InvoiceIn):
    _invoice_or_404(inv_id)
    database.update_invoice(inv_id, body.dict())
    return database.get_invoice_by_id(inv_id)


@app.delete("/invoices/{inv_id}", status_code=204)
def delete_invoice(inv_id: int):
    _invoice_or_404(inv_id)
    database.delete_invoice(inv_id)


_VALID_KINDS = {"lr", "party_bill", "driver_bill"}


@app.get("/invoices/{inv_id}/pdf/{kind}")
def invoice_pdf(inv_id: int, kind: str):
    if kind not in _VALID_KINDS:
        raise HTTPException(400, "kind must be one of: lr, party_bill, driver_bill")
    inv = _invoice_or_404(inv_id)
    pdf_bytes = render_pdf(kind, inv)
    filename = f"{inv['serial_number'].replace('/', '_')}_{kind}.pdf"
    return Response(
        pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/invoices/{inv_id}/pdf/all")
def invoice_pdf_all(inv_id: int):
    inv = _invoice_or_404(inv_id)
    blob = render_all_zip(inv)
    filename = f"{inv['serial_number'].replace('/', '_')}_all.zip"
    return Response(
        blob,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

⚠️ **Route ordering matters.** FastAPI matches routes top-down; `GET /invoices/next-serial` must appear before `GET /invoices/{inv_id}`, otherwise `"next-serial"` gets parsed as an int and 422s. The block above already orders them correctly — do not reorder.

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_invoices_api.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Run the full backend test suite**

Run: `pytest tests/ -v`
Expected: all existing + new tests PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/api.py tests/test_invoices_api.py
git commit -m "feat(invoices): REST API + PDF and ZIP download endpoints"
```

---

## Task 9: Frontend API helpers + route + sidebar entry + stub page

**Files:**
- Modify: `frontend/src/api.js`
- Modify: `frontend/src/App.jsx`
- Modify: `frontend/src/components/Sidebar.jsx`
- Create: `frontend/src/pages/InvoicesPage.jsx` (stub — real content in Task 10)

**Interfaces:**
- Consumes: backend endpoints from Task 8
- Produces:
  - `api.js` exports: `getInvoices`, `getInvoice(id)`, `createInvoice(data)`, `updateInvoice(id, data)`, `deleteInvoice(id)`, `nextSerial(date)`, `invoicePdfUrl(id, kind)`, `invoiceAllPdfsUrl(id)`
  - Route `/invoices` renders `InvoicesPage`
  - Sidebar shows "Invoices" entry (desktop link + mobile bottom-nav button)

- [ ] **Step 1: Add helpers to `frontend/src/api.js`**

Append to `frontend/src/api.js`:

```javascript
// ── Invoices ─────────────────────────────────────────────────────
export const getInvoices          = ()             => api.get('/invoices').then(r => r.data)
export const getInvoice           = (id)           => api.get(`/invoices/${id}`).then(r => r.data)
export const createInvoice        = (data)         => api.post('/invoices', data).then(r => r.data)
export const updateInvoice        = (id, data)     => api.put(`/invoices/${id}`, data).then(r => r.data)
export const deleteInvoice        = (id)           => api.delete(`/invoices/${id}`).then(r => r.data)
export const nextSerial           = (date)         => api.get('/invoices/next-serial', { params: { date } }).then(r => r.data.serial)
export const invoicePdfUrl        = (id, kind)     => `/api/invoices/${id}/pdf/${kind}`
export const invoiceAllPdfsUrl    = (id)           => `/api/invoices/${id}/pdf/all`
```

- [ ] **Step 2: Create the stub page**

Create `frontend/src/pages/InvoicesPage.jsx`:

```jsx
import React from 'react'
import { FileText } from 'lucide-react'

export default function InvoicesPage({ onNewInvoice }) {
  return (
    <div className="p-6">
      <div className="flex items-center gap-3">
        <FileText size={24} className="text-navy" />
        <h1 className="text-lg sm:text-xl font-bold text-navy">Invoices</h1>
      </div>
      <p className="mt-4 text-sm text-gray-500">Invoice list coming up in Task 10.</p>
    </div>
  )
}
```

- [ ] **Step 3: Register the route in `App.jsx`**

Open `frontend/src/App.jsx`. Add the import and the route:

```jsx
import InvoicesPage from './pages/InvoicesPage'
```

And inside `<Routes>`:

```jsx
<Route path="/invoices" element={<InvoicesPage />} />
```

Final file for reference (replace as needed, keeping the trip modal untouched):

```jsx
import React, { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import TripsPage from './pages/TripsPage'
import InsightsPage from './pages/InsightsPage'
import InvoicesPage from './pages/InvoicesPage'
import TripModal from './components/TripModal'

export default function App() {
  const [modal, setModal] = useState({ open: false, tripId: null })
  const [refreshKey, setRefreshKey] = useState(0)

  const openNew = () => setModal({ open: true, tripId: null })
  const openEdit = (id) => setModal({ open: true, tripId: id })
  const closeModal = () => setModal({ open: false, tripId: null })
  const onSaved = () => { closeModal(); setRefreshKey(k => k + 1) }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar onNewTrip={openNew} />
      <main className="flex-1 overflow-auto bg-page pt-14 md:pt-0 pb-16 md:pb-0">
        <Routes>
          <Route path="/"          element={<TripsPage onEditTrip={openEdit} refreshKey={refreshKey} />} />
          <Route path="/insights"  element={<InsightsPage />} />
          <Route path="/invoices"  element={<InvoicesPage />} />
        </Routes>
      </main>
      <TripModal open={modal.open} tripId={modal.tripId} onClose={closeModal} onSaved={onSaved} />
    </div>
  )
}
```

- [ ] **Step 4: Add sidebar entries**

Open `frontend/src/components/Sidebar.jsx`. Add `FileText` to the lucide import:

```jsx
import { Truck, List, PlusCircle, BarChart2, Download, FileText } from 'lucide-react'
```

Inside the **desktop** `<nav>`, after the Insights `NavLink`, add:

```jsx
          <NavLink to="/invoices" className={({ isActive }) => (isActive ? navActive : navInactive)}>
            <FileText size={18} />
            Invoices
          </NavLink>
```

Inside the **mobile bottom `<nav>`**, insert a NavLink before the Export button:

```jsx
        <NavLink to="/invoices" className={({ isActive }) => (isActive ? mobileNavActive : mobileNavInactive)}>
          <FileText size={20} />
          Invoices
        </NavLink>
```

- [ ] **Step 5: Verify the route renders**

Run the dev servers (in two terminals):
```
cd backend && python run.py            # or: uvicorn api:app --reload --port 8001
cd frontend && npm run dev
```
The Vite dev server on `http://localhost:5173` proxies `/api/*` → `http://127.0.0.1:8001/*` (path prefix stripped). Open `http://localhost:5173/invoices`. Expected: the stub page renders and the "Invoices" nav item is highlighted on desktop and mobile.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/api.js frontend/src/App.jsx frontend/src/components/Sidebar.jsx frontend/src/pages/InvoicesPage.jsx
git commit -m "feat(invoices): wire /invoices route and Sidebar nav (stub page)"
```

---

## Task 10: Flesh out `InvoicesPage.jsx` (list + KPIs + search + row actions)

**Files:**
- Modify: `frontend/src/pages/InvoicesPage.jsx`
- Modify: `frontend/src/App.jsx` (wire invoice modal state — mirrors trip modal)
- Create: `frontend/src/components/InvoiceModal.jsx` (empty stub — real form in Task 11)

**Interfaces:**
- Consumes: `getInvoices`, `deleteInvoice`, `invoicePdfUrl`, `invoiceAllPdfsUrl` from `api.js`; `ConfirmDialog`; `KpiCard`
- Produces: A functional list page that opens the (still-stub) `InvoiceModal` for New/Edit

- [ ] **Step 1: Create stub `InvoiceModal.jsx`**

Create `frontend/src/components/InvoiceModal.jsx`:

```jsx
import React from 'react'

export default function InvoiceModal({ open, invoiceId, onClose, onSaved }) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-2xl p-6 max-w-md">
        <div className="text-lg font-bold text-navy mb-2">Invoice Form (stub)</div>
        <div className="text-sm text-gray-500 mb-4">
          {invoiceId ? `Editing invoice #${invoiceId}` : 'New invoice'} — form UI arrives in Task 11.
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 rounded-lg text-sm bg-gray-200">Close</button>
          <button onClick={onSaved} className="px-4 py-2 rounded-lg text-sm bg-navy text-white">Simulate Save</button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Wire modal state in `App.jsx`**

Extend `App.jsx` with invoice modal state and pass an opener into `InvoicesPage`:

```jsx
import InvoiceModal from './components/InvoiceModal'

// inside App():
const [invModal, setInvModal] = useState({ open: false, invoiceId: null })
const [invRefreshKey, setInvRefreshKey] = useState(0)
const openNewInvoice  = () => setInvModal({ open: true, invoiceId: null })
const openEditInvoice = (id) => setInvModal({ open: true, invoiceId: id })
const closeInvModal   = () => setInvModal({ open: false, invoiceId: null })
const onInvSaved      = () => { closeInvModal(); setInvRefreshKey(k => k + 1) }
```

Update the invoices route and add the modal at the bottom:

```jsx
<Route path="/invoices" element={<InvoicesPage onNewInvoice={openNewInvoice} onEditInvoice={openEditInvoice} refreshKey={invRefreshKey} />} />
```

```jsx
<InvoiceModal open={invModal.open} invoiceId={invModal.invoiceId} onClose={closeInvModal} onSaved={onInvSaved} />
```

- [ ] **Step 3: Flesh out `InvoicesPage.jsx`**

Replace the stub with:

```jsx
import React, { useEffect, useMemo, useState } from 'react'
import { FileText, Search, X as XIcon, Edit2, Download, Trash2, Eye } from 'lucide-react'
import { getInvoices, deleteInvoice, invoicePdfUrl, invoiceAllPdfsUrl } from '../api'
import { KpiCard } from '../components/KpiCard'
import { ConfirmDialog } from '../components/ConfirmDialog'

const fmt = (n) => `₹${Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function InvoicesPage({ onNewInvoice, onEditInvoice, refreshKey }) {
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [confirm, setConfirm] = useState(null)
  const [downloadOpen, setDownloadOpen] = useState(null)  // invoice id whose menu is open

  const load = () => {
    setLoading(true)
    getInvoices().then(setInvoices).catch(() => setInvoices([])).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [refreshKey])

  const filtered = useMemo(() => {
    const q = search.toLowerCase().trim()
    if (!q) return invoices
    return invoices.filter(i =>
      i.serial_number?.toLowerCase().includes(q) ||
      i.vehicle_number?.toLowerCase().includes(q) ||
      i.consignor_name?.toLowerCase().includes(q) ||
      i.consignee_name?.toLowerCase().includes(q) ||
      i.from_location?.toLowerCase().includes(q) ||
      i.to_location?.toLowerCase().includes(q)
    )
  }, [invoices, search])

  const monthKey = new Date().toISOString().slice(0, 7)
  const thisMonth = invoices.filter(i => (i.date || '').startsWith(monthKey)).length
  const totalBilled = invoices.reduce((s, i) => s + (i.pb_amount_total || 0), 0)
  const latestSerial = invoices[0]?.serial_number || '—'

  const handleConfirm = async () => {
    if (!confirm) return
    try { await deleteInvoice(confirm.id) } catch { /* ignore */ }
    setConfirm(null); load()
  }

  return (
    <div className="p-3 sm:p-6 flex flex-col gap-4 sm:gap-5 min-h-full">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <FileText size={24} className="text-navy" />
          <h1 className="text-lg sm:text-xl font-bold text-navy">Invoices</h1>
        </div>
        <button
          onClick={onNewInvoice}
          className="bg-navy text-white font-semibold px-4 py-2 rounded-lg text-sm flex items-center gap-2 hover:bg-navy-light"
        >
          + New Invoice
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
        <KpiCard title="Total Invoices" value={invoices.length.toString()} accent="#1e3a5f" />
        <KpiCard title="This Month" value={thisMonth.toString()} accent="#f57c00" />
        <KpiCard title="Total Billed" value={fmt(totalBilled)} accent="#2e7d32" />
        <KpiCard title="Latest Serial" value={latestSerial} accent="#7b1fa2" />
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="flex items-center gap-2 px-3 sm:px-4 py-3 border-b border-gray-100">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search serial, vehicle, party, route…"
              className="w-full pl-8 pr-7 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy bg-white"
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700">
                <XIcon size={13} />
              </button>
            )}
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-gray-400 text-sm">Loading invoices…</div>
        ) : filtered.length === 0 ? (
          <div className="py-16 text-center text-gray-400 text-sm">
            {search ? 'No invoices match your search.' : 'No invoices yet. Click "New Invoice" to create your first one.'}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200 text-xs font-bold text-gray-500 uppercase">
                  <th className="text-left px-4 py-3">Serial #</th>
                  <th className="text-left px-4 py-3">Date</th>
                  <th className="text-left px-4 py-3">Vehicle</th>
                  <th className="text-left px-4 py-3">Consignor → Consignee</th>
                  <th className="text-left px-4 py-3">Route</th>
                  <th className="text-right px-4 py-3">Freight</th>
                  <th className="text-left px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((i, idx) => (
                  <tr key={i.id} className={`border-b border-gray-100 hover:bg-blue-50 ${idx % 2 === 1 ? 'bg-gray-50/30' : ''}`}>
                    <td className="px-4 py-3 font-bold text-navy whitespace-nowrap">{i.serial_number}</td>
                    <td className="px-4 py-3 text-gray-700 whitespace-nowrap">{i.date}</td>
                    <td className="px-4 py-3 font-mono font-bold text-navy whitespace-nowrap">{i.vehicle_number}</td>
                    <td className="px-4 py-3 text-gray-700">{[i.consignor_name, i.consignee_name].filter(Boolean).join(' → ') || '—'}</td>
                    <td className="px-4 py-3 text-gray-500">{[i.from_location, i.to_location].filter(Boolean).join(' → ') || '—'}</td>
                    <td className="px-4 py-3 text-right font-semibold">{fmt(i.pb_amount_total)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 relative">
                        <button title="View / Edit" onClick={() => onEditInvoice(i.id)} className="p-1.5 rounded hover:bg-blue-100 text-blue-600">
                          <Edit2 size={15} />
                        </button>
                        <button
                          title="Download PDFs"
                          onClick={() => setDownloadOpen(downloadOpen === i.id ? null : i.id)}
                          className="p-1.5 rounded hover:bg-green-100 text-green-600"
                        >
                          <Download size={15} />
                        </button>
                        {downloadOpen === i.id && (
                          <div className="absolute right-0 top-full mt-1 z-10 bg-white border border-gray-200 rounded-lg shadow-lg text-xs min-w-[160px]">
                            <a href={invoicePdfUrl(i.id, 'lr')} target="_blank" rel="noopener noreferrer" className="block px-3 py-2 hover:bg-gray-50">Download LR</a>
                            <a href={invoicePdfUrl(i.id, 'party_bill')} target="_blank" rel="noopener noreferrer" className="block px-3 py-2 hover:bg-gray-50">Download Party Bill</a>
                            <a href={invoicePdfUrl(i.id, 'driver_bill')} target="_blank" rel="noopener noreferrer" className="block px-3 py-2 hover:bg-gray-50">Download Driver Bill</a>
                            <a href={invoiceAllPdfsUrl(i.id)} target="_blank" rel="noopener noreferrer" className="block px-3 py-2 hover:bg-gray-50 border-t border-gray-100 font-semibold">All 3 (ZIP)</a>
                          </div>
                        )}
                        <button title="Delete" onClick={() => setConfirm({ id: i.id, serial: i.serial_number })} className="p-1.5 rounded hover:bg-red-100 text-red-500">
                          <Trash2 size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <ConfirmDialog
        open={!!confirm}
        message={confirm ? `Permanently delete invoice ${confirm.serial}? This cannot be undone.` : ''}
        confirmLabel="Delete"
        confirmColor="red"
        onCancel={() => setConfirm(null)}
        onConfirm={handleConfirm}
      />
    </div>
  )
}
```

- [ ] **Step 4: Verify in browser**

Restart dev servers if needed. Navigate to `/invoices`. Create a couple of invoices via the API (`curl -X POST` or use HTTP tab in your IDE) and verify:
- Rows appear in the list
- Search filters by serial/vehicle/party
- KPI cards update
- Download menu opens; clicking each PDF link opens/downloads a real PDF
- Delete button prompts and removes the row

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/InvoicesPage.jsx frontend/src/App.jsx frontend/src/components/InvoiceModal.jsx
git commit -m "feat(invoices): list page with search, KPIs, download menu, and delete"
```

---

## Task 11: `InvoiceModal.jsx` full form (5 sections + mirroring + save)

**Files:**
- Modify: `frontend/src/components/InvoiceModal.jsx`

**Interfaces:**
- Consumes: `getInvoice`, `createInvoice`, `updateInvoice`, `nextSerial`, `invoicePdfUrl`, `invoiceAllPdfsUrl` from `api.js`
- Produces: A full-featured modal used from `InvoicesPage`. On successful save, shows an inline success block with download links for LR / Party Bill / Driver Bill / All (ZIP), then calls `onSaved`.

- [ ] **Step 1: Replace `InvoiceModal.jsx` with the full form**

Replace `frontend/src/components/InvoiceModal.jsx`:

```jsx
import React, { useEffect, useMemo, useState } from 'react'
import { X, FileText, MapPin, Truck, CreditCard, Wrench, User } from 'lucide-react'
import { getInvoice, createInvoice, updateInvoice, nextSerial, invoicePdfUrl, invoiceAllPdfsUrl } from '../api'

const EMPTY = {
  date: new Date().toISOString().slice(0, 10),
  vehicle_number: '',
  from_location: '', to_location: '',
  consignor_name: '', consignor_address: '',
  consignee_name: '', consignee_address: '',
  lr_delivery_office_address: '',
  lr_packages: '', lr_description: '',
  lr_weight_nett: '', lr_weight_charged: '', lr_rate: '',
  lr_service_tax: '', lr_st_charge: '', lr_less_advance: '',
  lr_service_tax_payable_by: 'consignor',
  lr_insurance_risk: 'not_insured',
  lr_insurance_company: '', lr_insurance_policy_no: '',
  lr_insurance_policy_date: '', lr_insurance_amount: '',
  lr_ref_invoice_no: '', lr_ref_value: '', lr_ref_gst_no: '',
  pb_bill_to_name: '', pb_bill_to_address: '',
  pb_freight: '', pb_hamali: '', pb_halting: '',
  db_driver_name: '', db_driver_address: '', db_owner_phone: '',
  db_transport_party: '',
  db_fare: '', db_advance: '', db_collection: '',
  db_previous_balance: '', db_advance_deposited: '',
  db_expense_office: '', db_expense_collection_ac: '', db_expense_loan: '',
  db_expense_godown_crane: '', db_expense_st_charge: '',
}

const NUMERIC = new Set([
  'lr_packages','lr_weight_nett','lr_weight_charged','lr_rate',
  'lr_service_tax','lr_st_charge','lr_less_advance','lr_insurance_amount','lr_ref_value',
  'pb_freight','pb_hamali','pb_halting',
  'db_fare','db_advance','db_collection','db_previous_balance','db_advance_deposited',
  'db_expense_office','db_expense_collection_ac','db_expense_loan',
  'db_expense_godown_crane','db_expense_st_charge',
])

const inputCls = 'w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-navy focus:border-transparent'
const roCls    = inputCls + ' bg-gray-100 font-semibold'

function Field({ label, required, hint, children }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-semibold text-gray-600">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
        {hint && <span className="ml-2 text-[10px] font-bold uppercase text-amber-600">{hint}</span>}
      </label>
      {children}
    </div>
  )
}

function Section({ icon: Icon, title, color, children }) {
  return (
    <div className={`bg-${color}-50 rounded-xl p-4 sm:p-5`}>
      <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100">
        <Icon size={16} className="text-navy" />
        <span className="text-xs font-bold text-navy uppercase tracking-wider">{title}</span>
      </div>
      {children}
    </div>
  )
}

export default function InvoiceModal({ open, invoiceId, onClose, onSaved }) {
  const [form, setForm] = useState(EMPTY)
  const [dirty, setDirty] = useState(new Set())  // fields user has manually edited (opt out of mirroring)
  const [serialPreview, setSerialPreview] = useState('')
  const [savedId, setSavedId] = useState(null)   // shows download panel after save
  const [savedSerial, setSavedSerial] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!open) return
    setError('')
    setSavedId(null); setSavedSerial('')
    setDirty(new Set())
    if (invoiceId) {
      getInvoice(invoiceId).then(inv => {
        const next = { ...EMPTY }
        Object.keys(EMPTY).forEach(k => { next[k] = inv[k] ?? EMPTY[k]; if (NUMERIC.has(k)) next[k] = inv[k] != null ? String(inv[k]) : '' })
        setForm(next)
        setSerialPreview(inv.serial_number)
      })
    } else {
      setForm(EMPTY)
      nextSerial(EMPTY.date).then(setSerialPreview).catch(() => setSerialPreview(''))
    }
  }, [open, invoiceId])

  // Refresh serial preview when date crosses an FY boundary (new invoices only)
  useEffect(() => {
    if (!open || invoiceId) return
    nextSerial(form.date).then(setSerialPreview).catch(() => {})
  }, [form.date, open, invoiceId])

  // Mirroring: only for CREATE flow, and only for fields the user hasn't touched.
  const mirrorSet = (key, value) => {
    setForm(f => {
      if (dirty.has(key)) return f
      return { ...f, [key]: value }
    })
  }
  useEffect(() => { if (!invoiceId) mirrorSet('pb_bill_to_name', form.consignor_name) }, [form.consignor_name])
  useEffect(() => { if (!invoiceId) mirrorSet('pb_bill_to_address', form.consignor_address) }, [form.consignor_address])

  // Computed values (read-only fields shown to the user)
  const lrFreight = useMemo(() => (parseFloat(form.lr_weight_charged) || 0) * (parseFloat(form.lr_rate) || 0), [form.lr_weight_charged, form.lr_rate])
  const lrFinal   = useMemo(() => lrFreight + (parseFloat(form.lr_service_tax) || 0) + (parseFloat(form.lr_st_charge) || 0) - (parseFloat(form.lr_less_advance) || 0), [lrFreight, form.lr_service_tax, form.lr_st_charge, form.lr_less_advance])
  useEffect(() => { if (!invoiceId) mirrorSet('pb_freight', String(lrFreight || '')) }, [lrFreight])
  useEffect(() => { if (!invoiceId) mirrorSet('db_fare',    String(lrFreight || '')) }, [lrFreight])
  const pbTotal   = useMemo(() => (parseFloat(form.pb_freight) || 0) + (parseFloat(form.pb_hamali) || 0) + (parseFloat(form.pb_halting) || 0), [form.pb_freight, form.pb_hamali, form.pb_halting])
  const dbBalance = useMemo(() => (parseFloat(form.db_fare) || 0) - (parseFloat(form.db_advance) || 0), [form.db_fare, form.db_advance])
  const dbExpense = useMemo(() => ['db_expense_office','db_expense_collection_ac','db_expense_loan','db_expense_godown_crane','db_expense_st_charge']
    .reduce((s, k) => s + (parseFloat(form[k]) || 0), 0), [form])
  const dbSavings = dbBalance - dbExpense

  const set = (key) => (e) => {
    setDirty(d => { const nd = new Set(d); nd.add(key); return nd })
    setForm(f => ({ ...f, [key]: e.target.value }))
  }
  const setVal = (key, v) => {
    setDirty(d => { const nd = new Set(d); nd.add(key); return nd })
    setForm(f => ({ ...f, [key]: v }))
  }

  const handleSave = async () => {
    if (!form.date || !form.vehicle_number) { setError('Date and Vehicle Number are required.'); return }
    setSaving(true); setError('')
    try {
      // Convert numeric strings to numbers on the wire
      const payload = {}
      Object.keys(EMPTY).forEach(k => {
        payload[k] = NUMERIC.has(k) ? (parseFloat(form[k]) || 0) : (form[k] || '')
      })
      payload.vehicle_number = payload.vehicle_number.toUpperCase()
      if (invoiceId) {
        const updated = await updateInvoice(invoiceId, payload)
        setSavedId(invoiceId); setSavedSerial(updated.serial_number)
      } else {
        const res = await createInvoice(payload)
        setSavedId(res.id); setSavedSerial(res.serial_number)
      }
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to save invoice.')
    } finally {
      setSaving(false)
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl w-full sm:max-w-4xl max-h-[95vh] sm:max-h-[92vh] flex flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 bg-navy text-white">
          <div className="flex items-center gap-3">
            <FileText size={20} />
            <span className="text-base font-bold">
              {invoiceId ? 'Edit Invoice' : 'New Invoice'} · <span className="opacity-80 font-normal text-sm">{serialPreview}</span>
            </span>
          </div>
          <button onClick={onClose} className="hover:bg-white/20 rounded-lg p-1"><X size={20} /></button>
        </div>

        <div className="overflow-y-auto flex-1 p-4 sm:p-6 space-y-4 sm:space-y-6">

          <Section icon={FileText} title="Common Header" color="blue">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Field label="Serial #"><div className={roCls + ' font-mono text-navy'}>{serialPreview || '—'}</div></Field>
              <Field label="Date" required><input type="date" value={form.date} onChange={set('date')} className={inputCls} /></Field>
              <Field label="Vehicle Number" required>
                <input type="text" value={form.vehicle_number} onChange={set('vehicle_number')} placeholder="e.g. GJ01AB1234" className={inputCls + ' uppercase font-mono tracking-widest'} />
              </Field>
            </div>
          </Section>

          <Section icon={MapPin} title="Route & Parties" color="orange">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="From (Loading)"><input value={form.from_location} onChange={set('from_location')} className={inputCls} /></Field>
              <Field label="To (Unloading)"><input value={form.to_location} onChange={set('to_location')} className={inputCls} /></Field>
              <Field label="Consignor Name"><input value={form.consignor_name} onChange={set('consignor_name')} className={inputCls} /></Field>
              <Field label="Consignor Address"><input value={form.consignor_address} onChange={set('consignor_address')} className={inputCls} /></Field>
              <Field label="Consignee Name"><input value={form.consignee_name} onChange={set('consignee_name')} className={inputCls} /></Field>
              <Field label="Consignee Address"><input value={form.consignee_address} onChange={set('consignee_address')} className={inputCls} /></Field>
            </div>
          </Section>

          <Section icon={Truck} title="LR Details" color="green">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <div className="sm:col-span-2"><Field label="Delivery Office Address"><input value={form.lr_delivery_office_address} onChange={set('lr_delivery_office_address')} className={inputCls} /></Field></div>
              <Field label="Packages"><input type="number" min="0" value={form.lr_packages} onChange={set('lr_packages')} className={inputCls} /></Field>
              <Field label="Description (Said to Contain)"><input value={form.lr_description} onChange={set('lr_description')} className={inputCls} /></Field>
              <Field label="Weight Nett (kg)"><input type="number" min="0" step="0.01" value={form.lr_weight_nett} onChange={set('lr_weight_nett')} className={inputCls} /></Field>
              <Field label="Weight Charged (kg)"><input type="number" min="0" step="0.01" value={form.lr_weight_charged} onChange={set('lr_weight_charged')} className={inputCls} /></Field>
              <Field label="Rate (₹/kg)"><input type="number" min="0" step="0.01" value={form.lr_rate} onChange={set('lr_rate')} className={inputCls} /></Field>
              <Field label="Total Freight"><div className={roCls}>₹{lrFreight.toLocaleString('en-IN')}</div></Field>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              <Field label="Service Tax (₹)"><input type="number" min="0" value={form.lr_service_tax} onChange={set('lr_service_tax')} className={inputCls} /></Field>
              <Field label="St. Charge (₹)"><input type="number" min="0" value={form.lr_st_charge} onChange={set('lr_st_charge')} className={inputCls} /></Field>
              <Field label="Less Advance (₹)"><input type="number" min="0" value={form.lr_less_advance} onChange={set('lr_less_advance')} className={inputCls} /></Field>
            </div>
            <div className="mb-4">
              <label className="text-xs font-semibold text-gray-600 block mb-1">Service Tax Payable By</label>
              <div className="flex gap-4 text-sm">
                {['consignor','consignee','transporter'].map(v => (
                  <label key={v} className="flex items-center gap-2 capitalize">
                    <input type="radio" name="stp" checked={form.lr_service_tax_payable_by === v} onChange={() => setVal('lr_service_tax_payable_by', v)} />
                    {v}
                  </label>
                ))}
              </div>
            </div>
            <div className="border-t border-green-200 pt-4">
              <div className="text-xs font-bold text-navy mb-2">INSURANCE</div>
              <div className="flex gap-4 text-sm mb-3">
                <label className="flex items-center gap-2">
                  <input type="radio" name="risk" checked={form.lr_insurance_risk === 'not_insured'} onChange={() => setVal('lr_insurance_risk', 'not_insured')} />
                  Not insured (Owner's risk)
                </label>
                <label className="flex items-center gap-2">
                  <input type="radio" name="risk" checked={form.lr_insurance_risk === 'insured'} onChange={() => setVal('lr_insurance_risk', 'insured')} />
                  Insured
                </label>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <Field label="Company"><input value={form.lr_insurance_company} onChange={set('lr_insurance_company')} className={inputCls} /></Field>
                <Field label="Policy No"><input value={form.lr_insurance_policy_no} onChange={set('lr_insurance_policy_no')} className={inputCls} /></Field>
                <Field label="Policy Date"><input type="date" value={form.lr_insurance_policy_date} onChange={set('lr_insurance_policy_date')} className={inputCls} /></Field>
                <Field label="Amount"><input type="number" min="0" value={form.lr_insurance_amount} onChange={set('lr_insurance_amount')} className={inputCls} /></Field>
              </div>
            </div>
            <div className="border-t border-green-200 pt-4 mt-4">
              <div className="text-xs font-bold text-navy mb-2">REFERENCE (Consignor's own invoice)</div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Field label="Invoice No"><input value={form.lr_ref_invoice_no} onChange={set('lr_ref_invoice_no')} className={inputCls} /></Field>
                <Field label="Value (₹)"><input type="number" min="0" value={form.lr_ref_value} onChange={set('lr_ref_value')} className={inputCls} /></Field>
                <Field label="GST No"><input value={form.lr_ref_gst_no} onChange={set('lr_ref_gst_no')} className={inputCls} /></Field>
              </div>
            </div>
          </Section>

          <Section icon={CreditCard} title="Party Bill Details" color="purple">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Field label="Bill To Name" hint="mirrors consignor"><input value={form.pb_bill_to_name} onChange={set('pb_bill_to_name')} className={inputCls} /></Field>
              <Field label="Bill To Address" hint="mirrors consignor"><input value={form.pb_bill_to_address} onChange={set('pb_bill_to_address')} className={inputCls} /></Field>
              <Field label="Freight (₹)" hint="mirrors LR total"><input type="number" min="0" value={form.pb_freight} onChange={set('pb_freight')} className={inputCls} /></Field>
              <Field label="Hamali (₹)"><input type="number" min="0" value={form.pb_hamali} onChange={set('pb_hamali')} className={inputCls} /></Field>
              <Field label="Halting (₹)"><input type="number" min="0" value={form.pb_halting} onChange={set('pb_halting')} className={inputCls} /></Field>
              <Field label="Total Amount"><div className={roCls}>₹{pbTotal.toLocaleString('en-IN')}</div></Field>
            </div>
          </Section>

          <Section icon={User} title="Driver Bill Details" color="yellow">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
              <Field label="Driver / Owner Name"><input value={form.db_driver_name} onChange={set('db_driver_name')} className={inputCls} /></Field>
              <Field label="Owner Phone"><input type="tel" inputMode="numeric" maxLength={10} value={form.db_owner_phone} onChange={e => setVal('db_owner_phone', e.target.value.replace(/\D/g,'').slice(0,10))} className={inputCls} /></Field>
              <div className="sm:col-span-2"><Field label="Driver Address"><input value={form.db_driver_address} onChange={set('db_driver_address')} className={inputCls} /></Field></div>
              <div className="sm:col-span-2"><Field label="Transport Party (broker/agent)"><input value={form.db_transport_party} onChange={set('db_transport_party')} className={inputCls} /></Field></div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
              <Field label="Fare (₹)" hint="mirrors LR total"><input type="number" min="0" value={form.db_fare} onChange={set('db_fare')} className={inputCls} /></Field>
              <Field label="Advance (₹)"><input type="number" min="0" value={form.db_advance} onChange={set('db_advance')} className={inputCls} /></Field>
              <Field label="Balance Fare"><div className={roCls}>₹{dbBalance.toLocaleString('en-IN')}</div></Field>
              <Field label="Previous Balance"><input type="number" min="0" value={form.db_previous_balance} onChange={set('db_previous_balance')} className={inputCls} /></Field>
              <Field label="Advance Deposited"><input type="number" min="0" value={form.db_advance_deposited} onChange={set('db_advance_deposited')} className={inputCls} /></Field>
              <Field label="Collection (Vasuli)"><input type="number" min="0" value={form.db_collection} onChange={set('db_collection')} className={inputCls} /></Field>
            </div>
            <div className="border-t border-yellow-200 pt-4">
              <div className="text-xs font-bold text-navy mb-2">EXPENSES</div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-3">
                <Field label="Office Expense"><input type="number" min="0" value={form.db_expense_office} onChange={set('db_expense_office')} className={inputCls} /></Field>
                <Field label="Collection A/C"><input type="number" min="0" value={form.db_expense_collection_ac} onChange={set('db_expense_collection_ac')} className={inputCls} /></Field>
                <Field label="Loan"><input type="number" min="0" value={form.db_expense_loan} onChange={set('db_expense_loan')} className={inputCls} /></Field>
                <Field label="Godown Crane"><input type="number" min="0" value={form.db_expense_godown_crane} onChange={set('db_expense_godown_crane')} className={inputCls} /></Field>
                <Field label="Dala / Munshiyana / ST Charge"><input type="number" min="0" value={form.db_expense_st_charge} onChange={set('db_expense_st_charge')} className={inputCls} /></Field>
                <Field label="Total Expense"><div className={roCls}>₹{dbExpense.toLocaleString('en-IN')}</div></Field>
              </div>
            </div>
            <div className="bg-white rounded-lg p-3 border border-yellow-300 flex justify-between text-sm">
              <span className="font-semibold text-gray-700">Savings (Balance Fare − Total Expense)</span>
              <span className="font-bold text-green-700 text-lg">₹{dbSavings.toLocaleString('en-IN')}</span>
            </div>
          </Section>

          {savedId && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4">
              <div className="font-semibold text-green-800 mb-2">Invoice {savedSerial} saved. Download PDFs:</div>
              <div className="flex flex-wrap gap-2">
                <a href={invoicePdfUrl(savedId, 'lr')} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-white border border-green-300 text-sm hover:bg-green-100">LR</a>
                <a href={invoicePdfUrl(savedId, 'party_bill')} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-white border border-green-300 text-sm hover:bg-green-100">Party Bill</a>
                <a href={invoicePdfUrl(savedId, 'driver_bill')} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-white border border-green-300 text-sm hover:bg-green-100">Driver Bill</a>
                <a href={invoiceAllPdfsUrl(savedId)} target="_blank" rel="noopener noreferrer" className="px-3 py-1.5 rounded-lg bg-navy text-white text-sm hover:bg-navy-light font-semibold">All (ZIP)</a>
              </div>
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">{error}</div>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-4 sm:px-6 py-3 sm:py-4 bg-gray-50 border-t border-gray-200">
          <button onClick={onClose} className="flex-1 sm:flex-none px-5 py-2 rounded-lg text-sm font-medium text-gray-600 bg-white border border-gray-300 hover:bg-gray-100">
            {savedId ? 'Done' : 'Cancel'}
          </button>
          {!savedId && (
            <button onClick={handleSave} disabled={saving} className="flex-1 sm:flex-none px-6 py-2 rounded-lg text-sm font-bold text-white bg-navy hover:bg-navy-light disabled:opacity-50">
              {saving ? 'Saving…' : invoiceId ? 'Save Changes' : 'Save & Generate PDFs'}
            </button>
          )}
          {savedId && (
            <button onClick={onSaved} className="flex-1 sm:flex-none px-6 py-2 rounded-lg text-sm font-bold text-white bg-navy hover:bg-navy-light">Return to List</button>
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Manual E2E in browser**

Restart the dev servers. From `/invoices`, click **New Invoice**. Verify:
- Serial preview appears (`JB/YY-YY/NNN`) and updates when you change the date across the FY boundary
- Consignor name → auto-fills `Bill To Name` (until you edit the bill-to name manually; after that, further consignor edits don't overwrite it)
- Weight-charged × Rate → `Total Freight` shows the computed amount, and `pb_freight`, `db_fare` mirror it
- `Balance Fare`, `Total Expense`, `Savings` all recompute live
- Save → success block appears with 4 download links; clicking each opens/downloads a valid PDF
- Edit an existing invoice: fields pre-populate, save updates the row

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/InvoiceModal.jsx
git commit -m "feat(invoices): full 5-section modal form with mirroring, computed totals, and PDF downloads"
```

---

## Task 12: End-to-end smoke verification and cleanup

**Files:**
- Modify: `docs/superpowers/plans/2026-09-25-invoices-implementation.md` (this file — mark done)
- No new code files

- [ ] **Step 1: Full backend suite**

Run: `pytest tests/ -v`
Expected: everything passes, including pre-existing trip tests and all three new invoice test files.

- [ ] **Step 2: Frontend build**

Run: `cd frontend && npm run build`
Expected: build completes with no errors. Warnings acceptable.

- [ ] **Step 3: Manual golden-path checklist (in browser)**

- [ ] Sidebar (desktop): "Invoices" nav item highlights when on `/invoices`
- [ ] Sidebar (mobile viewport): "Invoices" bottom-nav button visible and works
- [ ] Create a new invoice with realistic values → serial matches current FY
- [ ] Edit the saved invoice → all fields pre-populate, save updates
- [ ] Download LR, Party Bill, Driver Bill individually — each opens a PDF that matches the mockup layout
- [ ] Download All (ZIP) — extracts to 3 PDFs
- [ ] Delete → confirmation prompt appears; row disappears
- [ ] Refresh page → data persisted in `trips.db`
- [ ] Existing `/` (trips) and `/insights` pages still work — no regressions

- [ ] **Step 4: Final commit**

If any small doc / naming cleanups came up during the walkthrough, fix and commit:

```bash
git add -A
git commit -m "chore(invoices): post-verification cleanup"
```

(Skip this commit if there's nothing to fix.)

---

## Self-review notes (author)

- **Spec coverage:** every §5 column, §6 serial rule, §7 endpoint, §8 template + filter, §9 UI element, §10 test is mapped to a task above.
- **Placeholders:** none — every step has runnable code or an exact command.
- **Type consistency:** `render_pdf(kind, invoice)`, `add_invoice(data) -> (id, serial)`, `nextSerial(date) -> string`, `invoicePdfUrl(id, kind) -> string` are consistent across all task blocks and match `api.js`.
- **Route ordering:** `GET /invoices/next-serial` is intentionally placed before `GET /invoices/{id}` (Task 8 Step 3).
- **Test file interdependency:** `test_invoices_pdf.py` and `test_invoices_api.py` both import `_minimal()` from `tests/test_invoices_db.py` — safe because pytest resolves modules by path and the `tests/__init__.py` package already exists.
