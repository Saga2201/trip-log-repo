# Invoices Feature — Design Spec

**Status:** Draft, awaiting user review
**Date:** 2026-09-25
**Owner:** sagarkoshti
**Reference mockup:** `docs/superpowers/mockups/invoices-mockup.html`

---

## 1. Purpose

Add an **Invoices** section to the JB Transport app that lets the user generate three linked billing PDFs from a single form:

1. **LR (Lorry Receipt)** — the consignment note handed at goods dispatch.
2. **Party Bill** — the bill sent to the consignor for freight collection.
3. **Driver Bill** — the internal settlement between the transporter and the driver / vehicle owner.

The three bills for one shipment share a single financial-year-scoped serial number (`JB/25-26/NNN`). Invoices are stored so the user can edit them later and regenerate the PDFs on demand. A QR-code slot is reserved in each PDF for a future scanner feature.

Invoices are **standalone** — they are not linked to the existing `trips` table. The user fills all invoice fields directly in the invoice form.

## 2. Non-goals

- No linkage to the existing `trips` records (explicit user decision — invoices are standalone).
- No PDF signing, no email-out, no payment tracking on invoices.
- No multi-line-item LR / Party Bill (one line per invoice set — matches the paper originals).
- No bilingual PDF output — **English only** for now (user decision).
- No live QR-code generation in this iteration; the PDF only reserves a visual slot.

## 3. User flow

1. User clicks **Invoices** in the sidebar → sees the invoices list.
2. Clicks **➕ New Invoice** → the *New Invoice* modal opens with an auto-generated serial preview.
3. User fills the five sections (Common Header, Route & Parties, LR Details, Party Bill Details, Driver Bill Details). Fields shared across bills auto-mirror between sections; totals auto-compute.
4. User clicks **Save & Generate All 3 PDFs**. The invoice row is persisted; the three PDFs are generated on the server and offered for download (individually or as a ZIP).
5. From the list, user can **View**, **Edit** (opens the same modal pre-filled), **Download** all 3 PDFs again, or **Delete** the invoice.

## 4. Architecture

React + FastAPI + SQLite (matching current stack). One new DB table, one new backend router, one new set of frontend pages/components, one PDF-templating layer.

```
┌──────────────────────────────────────────────────────┐
│ frontend/src/pages/InvoicesPage.jsx     (list)       │
│ frontend/src/components/InvoiceModal.jsx (form)      │
│ frontend/src/api.js  (add invoice endpoints)         │
└──────────────────────────────────────────────────────┘
                         │  HTTP
                         ▼
┌──────────────────────────────────────────────────────┐
│ backend/api.py         (add /invoices router)        │
│ backend/pdf/           (new module)                  │
│   ├── generator.py     (WeasyPrint wrapper)          │
│   └── templates/                                     │
│       ├── lr.html                                    │
│       ├── party_bill.html                            │
│       └── driver_bill.html                           │
│ database.py            (add invoices table + CRUD)   │
└──────────────────────────────────────────────────────┘
                         │
                         ▼
                    trips.db  (SQLite)
```

## 5. Data model

### Table: `invoices`

Single flat table. `INTEGER`/`REAL`/`TEXT`. All invoice-specific fields nullable so we can be lenient on partial saves during editing.

**Header (common)**

| Column                   | Type    | Notes                                           |
| ------------------------ | ------- | ----------------------------------------------- |
| `id`                     | INTEGER | PK autoincrement                                |
| `serial_number`          | TEXT    | Unique, format `JB/25-26/001` (see §6)          |
| `date`                   | TEXT    | ISO `YYYY-MM-DD`                                |
| `vehicle_number`         | TEXT    | Stored uppercase                                |
| `created_at`             | TEXT    | ISO timestamp                                   |
| `updated_at`             | TEXT    | ISO timestamp                                   |

**Route & Parties**

| Column                   | Type    |
| ------------------------ | ------- |
| `from_location`          | TEXT    |
| `to_location`            | TEXT    |
| `consignor_name`         | TEXT    |
| `consignor_address`      | TEXT    |
| `consignee_name`         | TEXT    |
| `consignee_address`      | TEXT    |

**LR-specific**

| Column                        | Type | Notes                                         |
| ----------------------------- | ---- | --------------------------------------------- |
| `lr_delivery_office_address`  | TEXT |                                               |
| `lr_packages`                 | INTEGER |                                            |
| `lr_description`              | TEXT |                                               |
| `lr_weight_nett`              | REAL |                                               |
| `lr_weight_charged`           | REAL |                                               |
| `lr_rate`                     | REAL | ₹ per unit weight                             |
| `lr_freight_total`            | REAL | Computed = `weight_charged * rate`, overridable |
| `lr_service_tax`              | REAL |                                               |
| `lr_st_charge`                | REAL |                                               |
| `lr_less_advance`             | REAL |                                               |
| `lr_final_total`              | REAL | Computed = `freight_total + s_tax + st_ch − less_adv` |
| `lr_service_tax_payable_by`   | TEXT | One of `'consignor' \| 'consignee' \| 'transporter'` |
| `lr_insurance_risk`           | TEXT | `'insured' \| 'not_insured'`                  |
| `lr_insurance_company`        | TEXT |                                               |
| `lr_insurance_policy_no`      | TEXT |                                               |
| `lr_insurance_policy_date`    | TEXT |                                               |
| `lr_insurance_amount`         | REAL |                                               |
| `lr_ref_invoice_no`           | TEXT | Consignor's own invoice number                |
| `lr_ref_value`                | REAL | Value of goods                                |
| `lr_ref_gst_no`               | TEXT | Consignor's GST number                        |

**Party Bill-specific**

| Column               | Type | Notes                                          |
| -------------------- | ---- | ---------------------------------------------- |
| `pb_bill_to_name`    | TEXT | Mirrors `consignor_name` on create; editable   |
| `pb_bill_to_address` | TEXT | Mirrors `consignor_address` on create          |
| `pb_freight`         | REAL | Mirrors `lr_freight_total`                     |
| `pb_hamali`          | REAL |                                                |
| `pb_halting`         | REAL |                                                |
| `pb_amount_total`    | REAL | Computed = `freight + hamali + halting`        |

**Driver Bill-specific**

| Column                       | Type | Notes                                        |
| ---------------------------- | ---- | -------------------------------------------- |
| `db_driver_name`             | TEXT |                                              |
| `db_driver_address`          | TEXT |                                              |
| `db_owner_phone`             | TEXT | 10-digit                                     |
| `db_transport_party`         | TEXT | Broker / booking party                       |
| `db_fare`                    | REAL | Soft-mirrors `lr_freight_total` on form open; driver's contracted rate often differs from party billed freight (transporter's margin), so the field is expected to be edited. |
| `db_advance`                 | REAL |                                              |
| `db_balance_fare`            | REAL | Computed = `fare − advance`                  |
| `db_collection`              | REAL | (Vasuli)                                     |
| `db_previous_balance`        | REAL |                                              |
| `db_advance_deposited`       | REAL |                                              |
| `db_expense_office`          | REAL |                                              |
| `db_expense_collection_ac`   | REAL |                                              |
| `db_expense_loan`            | REAL |                                              |
| `db_expense_godown_crane`    | REAL |                                              |
| `db_expense_st_charge`       | REAL | Dala / Munshiyana / ST                       |
| `db_expense_total`           | REAL | Computed = sum of the 5 expense columns      |
| `db_savings`                 | REAL | Computed = `balance_fare − expense_total`    |

### Table: `invoice_sequences`

Small helper table to atomically allocate the next number per financial year.

| Column           | Type    | Notes                              |
| ---------------- | ------- | ---------------------------------- |
| `financial_year` | TEXT PK | e.g. `'25-26'`                     |
| `last_seq`       | INTEGER | Last allocated sequence for FY     |

## 6. Serial number generation

Format: `JB/YY-YY/NNN` (e.g. `JB/25-26/024`).

- **Financial Year** for a given `date`: April 1 → March 31.
  - If `date.month >= 4`: FY = `f"{yr%100:02d}-{(yr+1)%100:02d}"`
  - Else:                 FY = `f"{(yr-1)%100:02d}-{yr%100:02d}"`
- **Sequence** is a per-FY counter. `NNN` is zero-padded to 3 digits; grows past 3 digits if needed (`JB/25-26/1024`).
- Allocation happens **inside a DB transaction** on insert: upsert `invoice_sequences` row, take `last_seq + 1`, format serial, insert invoice.
- Serial is **immutable** after creation (edits do not renumber; the `date` field can change, but the serial's FY prefix does not).

## 7. Backend API

New file: `backend/api.py` (extend existing router). All under `/invoices`.

| Method | Path                                     | Purpose                                |
| ------ | ---------------------------------------- | -------------------------------------- |
| GET    | `/invoices`                              | List all invoices (newest first).      |
| POST   | `/invoices`                              | Create; server allocates serial.       |
| GET    | `/invoices/{id}`                         | Fetch one for editing.                 |
| PUT    | `/invoices/{id}`                         | Update (serial unchanged).             |
| DELETE | `/invoices/{id}`                         | Delete.                                |
| GET    | `/invoices/{id}/pdf/{kind}`              | Stream one PDF; `kind` ∈ `lr` \| `party_bill` \| `driver_bill`. |
| GET    | `/invoices/{id}/pdf/all`                 | Stream a ZIP of all 3 PDFs.            |
| GET    | `/invoices/next-serial?date=YYYY-MM-DD`  | Returns `{ serial: "JB/25-26/025" }` — preview only, not allocated. Called by the form to show the user what serial they'll get. |

**Pydantic model:** `InvoiceIn` with all writable fields (serial excluded — server-owned). Response shape includes the allocated `serial_number` and any server-computed totals.

**Enrichment:** Compute totals server-side on read (mirrors current `_enrich` pattern for trips) so the frontend always renders authoritative numbers.

## 8. PDF generation

**Library:** WeasyPrint (`pip install weasyprint`). Renders HTML + CSS to PDF. Chosen because layouts are dense-tabular and change requests are easier in HTML/CSS than in ReportLab primitives.

**Templates:** Jinja2 HTML in `backend/pdf/templates/`:
- `lr.html`
- `party_bill.html`
- `driver_bill.html`
- `_base.css` — shared print styles (A4, margins, borders, fonts)

Each template consumes the invoice dict and renders one A4 page.

**QR slot:** Every template includes a `<div class="qr-slot">` in the header area (~60×60 px). The current build fills it with a placeholder pattern. When the QR feature ships, the slot is replaced with a QR image encoding `${APP_URL}/invoices/${serial_number}`.

**Fonts:** Rely on system-installed serif for now. If we hit font gaps, bundle Noto Sans and Noto Sans Devanagari (Devanagari for future bilingual mode).

**Company header constants** (name, address, phones, PAN) are static across all invoices for JB Transport. They live in a single Python module (`backend/pdf/company.py`) as a plain dict and are passed to every template render. This keeps them out of the DB (they'd be duplicated on every row) and out of the templates (so they're editable in one place).

```python
# backend/pdf/company.py
COMPANY = {
    "name": "JB Transports",
    "address": "201, Shine Swasti, Nr. Godrej Garden City, Gota, Ahmedabad-382470",
    "jurisdiction": "Ahmedabad",
    "contact_person": "Dattaji Patil",
    "phones": ["7600224710", "9328448057"],
    "pan": "AUWPB0355R",
    "logo_path": "backend/pdf/assets/jb_logo.png",
}
```

**Amount-in-words** (Party Bill footer): rendered in the template using [`num2words`](https://pypi.org/project/num2words/) with the `lang='en_IN'` locale for Indian numbering (Lakh/Crore). Called from a Jinja filter `{{ pb_amount_total | inr_words }}`.

**Dependencies to add to `backend/requirements.txt`:**
- `weasyprint>=60`
- `jinja2>=3.1`
- `num2words>=0.5.13`

## 9. Frontend

### New files

```
frontend/src/pages/InvoicesPage.jsx        # list + KPIs + search
frontend/src/components/InvoiceModal.jsx   # 5-section form
```

### Modified files

```
frontend/src/api.js         # add invoice API helpers
frontend/src/App.jsx        # register /invoices route + modal state
frontend/src/components/Sidebar.jsx  # add 'Invoices' nav item (desktop + mobile)
```

### Form behavior (`InvoiceModal.jsx`)

- Modal shell mirrors `TripModal.jsx` (bottom-sheet on mobile, centered dialog on desktop).
- Sections are **always visible** (scrollable), matching the mockup — no accordion in v1.
- **Mirrored fields** initialize from their source but decouple on user edit (a `dirty` flag per mirrored field prevents future auto-overwrites in the same form session).
- **Computed fields** are always derived — displayed read-only, styled with the gray `bg-gray-100` treatment used elsewhere.
- Serial preview: on modal open, hit `GET /invoices/next-serial?date=YYYY-MM-DD` (new endpoint) to show what will be allocated. Actual allocation happens server-side at save. If the user changes the date across the FY boundary, refetch the preview.
- Validation: `date`, `vehicle_number` required. Everything else optional.
- Save flow:
  1. `POST /invoices` (or `PUT` if editing).
  2. Trigger downloads: user can click "Download LR", "Download Party Bill", "Download Driver Bill", or "Download All (ZIP)" from a success dialog. Downloads use `/invoices/{id}/pdf/{kind}`.

### List page (`InvoicesPage.jsx`)

- Header + KPI cards (Total Invoices, This Month, Total Billed, Current FY sequence label).
- Search input filters by `serial_number`, `vehicle_number`, `consignor_name`, `consignee_name`.
- Optional date-range filter (parity with trips list can be a v1.1 nice-to-have — v1 has search only).
- Table columns: Serial, Date, Vehicle, Consignor → Consignee, Route, Freight (`pb_amount_total`), Actions.
- Actions per row: View (opens read-only modal reusing InvoiceModal), Edit, Download (opens dropdown for the 3 kinds + ZIP), Delete (with `ConfirmDialog`).

## 10. Testing

- **Backend unit tests** (`tests/`):
  - Serial allocation: sequential within FY; resets across FY boundary; concurrent allocation stays unique (simulate with two rapid POSTs in a single test).
  - CRUD round-trip: create → get → update → delete.
  - Computed fields: `lr_freight_total`, `pb_amount_total`, `db_balance_fare`, `db_expense_total`, `db_savings`.
- **PDF smoke tests**: for a saved invoice, render each of the 3 PDFs and assert (a) response is `application/pdf`, (b) size > 1 KB, (c) contains the serial number byte sequence.
- **Frontend**: manual smoke test in the browser — create, edit, delete, download, verify layout on a fresh install.

## 11. Migration & rollout

- Non-destructive additive migration: `database.init_db()` gets `CREATE TABLE IF NOT EXISTS invoices` and `CREATE TABLE IF NOT EXISTS invoice_sequences`. No changes to `trips`.
- No env config needed; WeasyPrint deps installed via `backend/requirements.txt`.
- No auth on `/invoices/*` — matches the current app's trust model (single-user local install).

## 12. Future scope (out of this spec)

- **QR wiring**: swap `qr-slot` placeholder for a real QR image linking to `/invoices/{serial}` (read-only detail view).
- **Optional trip linkage**: add nullable `trip_id` column and a "Load from trip" picker in the form.
- **Bilingual toggle**: switch Driver Bill to Hindi/Marathi via a template variant.
- **Email / WhatsApp send** of the PDF from the app.
- **Multi-line-item** LR and Party Bill for shipments with multiple consignments.

## 13. Open questions

None at spec time. Any that surface during implementation planning will be raised via the writing-plans skill.
