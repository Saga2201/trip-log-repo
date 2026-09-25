# Material & Weight Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `material` (free-text cargo name) and `material_weight` (stored in kg, displayed as tonnes) fields to every layer of the TripLog app — DB, backend API, NiceGUI UI, React UI, and Excel export.

**Architecture:** SQLite migration adds two new columns with defaults so existing records are unaffected. The FastAPI backend threads the fields through its Pydantic model and all `database.*` calls. Both UIs (NiceGUI and React) expose the fields in the Route section of the trip form and show weight converted to tonnes in the list table. Export gains two new columns.

**Tech Stack:** Python / SQLite (`database.py`), FastAPI / Pydantic (`backend/api.py`), NiceGUI (`ui/trips.py`), React + Tailwind (`frontend/src/`), openpyxl (`export.py`), pytest (`tests/`)

---

## File Map

| File | Change |
|---|---|
| `database.py` | Add `material`, `material_weight` columns + migration; update `add_trip` / `update_trip` signatures & SQL |
| `backend/api.py` | Add fields to `TripIn`; thread through `create_trip`, `update_trip`, `upload_image`, `delete_image` |
| `export.py` | Add `Material` and `Weight (T)` columns |
| `ui/trips.py` | Add form fields in Route section; add columns to NiceGUI table |
| `frontend/src/components/TripModal.jsx` | Add fields to `EMPTY_FORM`, form UI, and `handleSave` payload |
| `frontend/src/pages/TripsPage.jsx` | Add Material and Weight columns to the table |
| `tests/test_database.py` | New tests for material/weight round-trip |
| `tests/test_export.py` | New test: export includes Material and Weight (T) columns |

---

## Task 1: Database — add columns, migration, and updated signatures

**Files:**
- Modify: `database.py`
- Test: `tests/test_database.py`

- [ ] **Step 1: Write failing tests for the new fields**

Append to `tests/test_database.py`:

```python
def test_add_trip_with_material_and_weight():
    trip_id = database.add_trip(
        date='2026-05-23',
        vehicle_number='GJ 01 AB 1234',
        state='Gujarat', city='Surat',
        driver_phone='', owner_phone='',
        loading_address='Surat Market',
        unloading_address='Mumbai Hub',
        total_booking=15000.0,
        material='Cotton Bales',
        material_weight=8500.0,  # kg
    )
    trip = database.get_trip_by_id(trip_id)
    assert trip['material'] == 'Cotton Bales'
    assert trip['material_weight'] == 8500.0


def test_update_trip_material_and_weight():
    database.add_trip(
        date='2026-05-23',
        vehicle_number='GJ 01 AB 1234',
        state='Gujarat', city='Surat',
        driver_phone='', owner_phone='',
        loading_address='Surat Market',
        unloading_address='Mumbai Hub',
        total_booking=15000.0,
    )
    database.update_trip(
        trip_id=1,
        date='2026-05-23',
        vehicle_number='GJ 01 AB 1234',
        state='Gujarat', city='Surat',
        driver_phone='', owner_phone='',
        loading_address='Surat Market',
        unloading_address='Mumbai Hub',
        total_booking=15000.0,
        material='Steel Rods',
        material_weight=12000.0,
    )
    trip = database.get_trip_by_id(1)
    assert trip['material'] == 'Steel Rods'
    assert trip['material_weight'] == 12000.0


def test_material_defaults_to_empty_for_old_trips():
    """Simulates a trip created without material fields (migration path)."""
    trip_id = database.add_trip(
        date='2026-05-23',
        vehicle_number='RJ 14 CD 9012',
        state='Rajasthan', city='Jaipur',
        driver_phone='', owner_phone='',
        loading_address='Jaipur', unloading_address='Delhi',
        total_booking=5000.0,
    )
    trip = database.get_trip_by_id(trip_id)
    assert trip['material'] == ''
    assert trip['material_weight'] == 0.0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -m pytest tests/test_database.py::test_add_trip_with_material_and_weight tests/test_database.py::test_update_trip_material_and_weight tests/test_database.py::test_material_defaults_to_empty_for_old_trips -v
```

Expected: FAIL — `add_trip() got an unexpected keyword argument 'material'`

- [ ] **Step 3: Update `database.py` — migration, `add_trip`, `update_trip`**

Replace the full `database.py` with:

```python
import sqlite3
import os
from datetime import datetime
from pathlib import Path

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trips.db')
IMAGES_DIR = Path(DB_PATH).parent / 'payment_images'


def _get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    with _get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                vehicle_number TEXT NOT NULL,
                state TEXT DEFAULT '',
                city TEXT DEFAULT '',
                driver_phone TEXT DEFAULT '',
                owner_phone TEXT DEFAULT '',
                loading_address TEXT NOT NULL,
                unloading_address TEXT NOT NULL,
                total_booking REAL NOT NULL,
                payment_1 REAL DEFAULT 0,
                payment_2 REAL DEFAULT 0,
                payment_3 REAL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        ''')
        # migrate: add columns to existing databases
        existing = {row[1] for row in conn.execute('PRAGMA table_info(trips)')}
        for col in ('payment_1_image', 'payment_2_image', 'payment_3_image'):
            if col not in existing:
                conn.execute(f'ALTER TABLE trips ADD COLUMN {col} TEXT')
        if 'completed' not in existing:
            conn.execute('ALTER TABLE trips ADD COLUMN completed INTEGER DEFAULT 0')
        if 'party_name' not in existing:
            conn.execute("ALTER TABLE trips ADD COLUMN party_name TEXT DEFAULT ''")
        if 'party_contact' not in existing:
            conn.execute("ALTER TABLE trips ADD COLUMN party_contact TEXT DEFAULT ''")
        if 'note' not in existing:
            conn.execute("ALTER TABLE trips ADD COLUMN note TEXT DEFAULT ''")
        if 'material' not in existing:
            conn.execute("ALTER TABLE trips ADD COLUMN material TEXT DEFAULT ''")
        if 'material_weight' not in existing:
            conn.execute('ALTER TABLE trips ADD COLUMN material_weight REAL DEFAULT 0')
        conn.commit()


def add_trip(date, vehicle_number, state, city, driver_phone, owner_phone,
             loading_address, unloading_address, total_booking,
             payment_1=0.0, payment_2=0.0, payment_3=0.0,
             payment_1_image=None, payment_2_image=None, payment_3_image=None,
             party_name='', party_contact='', note='',
             material='', material_weight=0.0):
    with _get_conn() as conn:
        cursor = conn.execute('''
            INSERT INTO trips (date, vehicle_number, state, city, driver_phone, owner_phone,
                loading_address, unloading_address, total_booking,
                payment_1, payment_2, payment_3, created_at,
                payment_1_image, payment_2_image, payment_3_image,
                party_name, party_contact, note,
                material, material_weight)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, vehicle_number, state, city, driver_phone, owner_phone,
              loading_address, unloading_address, total_booking,
              payment_1, payment_2, payment_3, datetime.now().isoformat(),
              payment_1_image, payment_2_image, payment_3_image,
              party_name, party_contact, note,
              material, material_weight))
        conn.commit()
        return cursor.lastrowid


def get_all_trips():
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM trips ORDER BY date DESC, id DESC')
        return [dict(row) for row in cursor.fetchall()]


def get_trip_by_id(trip_id):
    with _get_conn() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('SELECT * FROM trips WHERE id = ?', (trip_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_trip(trip_id, date, vehicle_number, state, city, driver_phone, owner_phone,
                loading_address, unloading_address, total_booking,
                payment_1=0.0, payment_2=0.0, payment_3=0.0,
                payment_1_image=None, payment_2_image=None, payment_3_image=None,
                party_name='', party_contact='', note='',
                material='', material_weight=0.0):
    with _get_conn() as conn:
        conn.execute('''
            UPDATE trips SET date=?, vehicle_number=?, state=?, city=?,
                driver_phone=?, owner_phone=?, loading_address=?,
                unloading_address=?, total_booking=?,
                payment_1=?, payment_2=?, payment_3=?,
                payment_1_image=?, payment_2_image=?, payment_3_image=?,
                party_name=?, party_contact=?, note=?,
                material=?, material_weight=?
            WHERE id=?
        ''', (date, vehicle_number, state, city, driver_phone, owner_phone,
              loading_address, unloading_address, total_booking,
              payment_1, payment_2, payment_3,
              payment_1_image, payment_2_image, payment_3_image,
              party_name, party_contact, note,
              material, material_weight,
              trip_id))
        conn.commit()


def set_completed(trip_id, completed: bool):
    with _get_conn() as conn:
        conn.execute('UPDATE trips SET completed = ? WHERE id = ?', (1 if completed else 0, trip_id))
        conn.commit()


def delete_trip(trip_id):
    trip = get_trip_by_id(trip_id)
    if trip:
        for col in ('payment_1_image', 'payment_2_image', 'payment_3_image'):
            path = trip.get(col)
            if path:
                Path(path).unlink(missing_ok=True)
    with _get_conn() as conn:
        conn.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
        conn.commit()
```

- [ ] **Step 4: Run all database tests**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -m pytest tests/test_database.py -v
```

Expected: All 8 tests PASS (5 existing + 3 new).

- [ ] **Step 5: Commit**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
git add database.py tests/test_database.py
git commit -m "feat: add material and material_weight columns to DB"
```

---

## Task 2: Backend API — thread new fields through FastAPI

**Files:**
- Modify: `backend/api.py`

- [ ] **Step 1: Update `TripIn` Pydantic model**

In `backend/api.py`, find the `TripIn` class and add the two new fields after `note`:

```python
class TripIn(BaseModel):
    date: str
    vehicle_number: str
    state: str = ''
    city: str = ''
    driver_phone: str = ''
    owner_phone: str = ''
    party_name: str = ''
    party_contact: str = ''
    note: str = ''
    material: str = ''
    material_weight: float = 0.0
    loading_address: str
    unloading_address: str
    total_booking: float
    payment_1: float = 0.0
    payment_2: float = 0.0
    payment_3: float = 0.0
    payment_1_image: Optional[str] = None
    payment_2_image: Optional[str] = None
    payment_3_image: Optional[str] = None
```

- [ ] **Step 2: Update `create_trip` endpoint**

Find the `create_trip` function. Add `material` and `material_weight` to the `database.add_trip(...)` call:

```python
@app.post('/trips', status_code=201)
def create_trip(body: TripIn):
    trip_id = database.add_trip(
        date=body.date,
        vehicle_number=body.vehicle_number,
        state=body.state,
        city=body.city,
        driver_phone=body.driver_phone,
        owner_phone=body.owner_phone,
        loading_address=body.loading_address,
        unloading_address=body.unloading_address,
        total_booking=body.total_booking,
        payment_1=body.payment_1,
        payment_2=body.payment_2,
        payment_3=body.payment_3,
        payment_1_image=body.payment_1_image,
        payment_2_image=body.payment_2_image,
        payment_3_image=body.payment_3_image,
        party_name=body.party_name,
        party_contact=body.party_contact,
        note=body.note,
        material=body.material,
        material_weight=body.material_weight,
    )
    return {'id': trip_id}
```

- [ ] **Step 3: Update `update_trip` endpoint**

Find the `update_trip` function. Add `material` and `material_weight` to the `database.update_trip(...)` call:

```python
@app.put('/trips/{trip_id}')
def update_trip(trip_id: int, body: TripIn):
    _trip_or_404(trip_id)
    database.update_trip(
        trip_id=trip_id,
        date=body.date,
        vehicle_number=body.vehicle_number,
        state=body.state,
        city=body.city,
        driver_phone=body.driver_phone,
        owner_phone=body.owner_phone,
        loading_address=body.loading_address,
        unloading_address=body.unloading_address,
        total_booking=body.total_booking,
        payment_1=body.payment_1,
        payment_2=body.payment_2,
        payment_3=body.payment_3,
        payment_1_image=body.payment_1_image,
        payment_2_image=body.payment_2_image,
        payment_3_image=body.payment_3_image,
        party_name=body.party_name,
        party_contact=body.party_contact,
        note=body.note,
        material=body.material,
        material_weight=body.material_weight,
    )
    return _enrich(database.get_trip_by_id(trip_id))
```

- [ ] **Step 4: Update `upload_image` endpoint**

Find the `upload_image` function. The inner `database.update_trip(...)` call must preserve the new fields from the existing trip. Add `material` and `material_weight`:

```python
    database.update_trip(
        trip_id=trip_id,
        date=trip['date'],
        vehicle_number=trip['vehicle_number'],
        state=trip.get('state', ''),
        city=trip.get('city', ''),
        driver_phone=trip.get('driver_phone', ''),
        owner_phone=trip.get('owner_phone', ''),
        loading_address=trip['loading_address'],
        unloading_address=trip['unloading_address'],
        total_booking=trip['total_booking'],
        payment_1=trip.get('payment_1', 0.0),
        payment_2=trip.get('payment_2', 0.0),
        payment_3=trip.get('payment_3', 0.0),
        payment_1_image=str(dest) if n == 1 else trip.get('payment_1_image'),
        payment_2_image=str(dest) if n == 2 else trip.get('payment_2_image'),
        payment_3_image=str(dest) if n == 3 else trip.get('payment_3_image'),
        party_name=trip.get('party_name', ''),
        party_contact=trip.get('party_contact', ''),
        note=trip.get('note', ''),
        material=trip.get('material', ''),
        material_weight=trip.get('material_weight', 0.0),
    )
```

- [ ] **Step 5: Update `delete_image` endpoint**

Find the `delete_image` function. Same pattern — preserve the new fields:

```python
    database.update_trip(
        trip_id=trip_id,
        date=trip['date'],
        vehicle_number=trip['vehicle_number'],
        state=trip.get('state', ''),
        city=trip.get('city', ''),
        driver_phone=trip.get('driver_phone', ''),
        owner_phone=trip.get('owner_phone', ''),
        loading_address=trip['loading_address'],
        unloading_address=trip['unloading_address'],
        total_booking=trip['total_booking'],
        payment_1=trip.get('payment_1', 0.0),
        payment_2=trip.get('payment_2', 0.0),
        payment_3=trip.get('payment_3', 0.0),
        payment_1_image=None if n == 1 else trip.get('payment_1_image'),
        payment_2_image=None if n == 2 else trip.get('payment_2_image'),
        payment_3_image=None if n == 3 else trip.get('payment_3_image'),
        party_name=trip.get('party_name', ''),
        party_contact=trip.get('party_contact', ''),
        note=trip.get('note', ''),
        material=trip.get('material', ''),
        material_weight=trip.get('material_weight', 0.0),
    )
```

- [ ] **Step 6: Smoke-test the backend starts without error**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -c "import sys; sys.path.insert(0, 'backend'); import api; print('API import OK')"
```

Expected output: `API import OK`

- [ ] **Step 7: Commit**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
git add backend/api.py
git commit -m "feat: add material and material_weight to FastAPI TripIn and all endpoints"
```

---

## Task 3: Export — add Material and Weight (T) columns

**Files:**
- Modify: `export.py`
- Test: `tests/test_export.py`

- [ ] **Step 1: Write failing tests**

Append to `tests/test_export.py`:

```python
def test_export_includes_material_and_weight_columns(tmp_path):
    trips_with_material = [
        {**SAMPLE_TRIPS[0], 'material': 'Cotton Bales', 'material_weight': 8500.0},
        {**SAMPLE_TRIPS[1], 'material': '',             'material_weight': 0.0},
    ]
    out_path = export_to_excel(trips_with_material, dest_dir=str(tmp_path))
    wb = openpyxl.load_workbook(out_path)
    ws = wb.active
    headers = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
    assert 'Material' in headers
    assert 'Weight (T)' in headers


def test_export_weight_converted_to_tonnes(tmp_path):
    trips_with_material = [
        {**SAMPLE_TRIPS[0], 'material': 'Steel Rods', 'material_weight': 12000.0},
        {**SAMPLE_TRIPS[1], 'material': '',            'material_weight': 0.0},
    ]
    out_path = export_to_excel(trips_with_material, dest_dir=str(tmp_path))
    wb = openpyxl.load_workbook(out_path)
    ws = wb.active
    headers = [ws.cell(1, col).value for col in range(1, ws.max_column + 1)]
    weight_col = headers.index('Weight (T)') + 1
    material_col = headers.index('Material') + 1
    # row 2 = first trip: 12000 kg → 12.0 T
    assert ws.cell(2, weight_col).value == 12.0
    assert ws.cell(2, material_col).value == 'Steel Rods'
    # row 3 = second trip: 0 kg → 0.0 T
    assert ws.cell(3, weight_col).value == 0.0
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -m pytest tests/test_export.py::test_export_includes_material_and_weight_columns tests/test_export.py::test_export_weight_converted_to_tonnes -v
```

Expected: FAIL — `AssertionError: 'Material' not in headers`

- [ ] **Step 3: Update `export.py`**

Replace the full `export.py` with:

```python
import os
from datetime import date
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from helpers import calc_pending, calc_received, calc_status

HEADERS = [
    'Date', 'Vehicle Number', 'State', 'City',
    'Driver Phone', 'Owner Phone',
    'Loading Address', 'Unloading Address',
    'Total Booking (₹)', 'Payment 1 (₹)', 'Payment 2 (₹)', 'Payment 3 (₹)',
    'Material', 'Weight (T)',
    'Received (₹)', 'Pending (₹)', 'Status',
]

FIELD_MAP = [
    'date', 'vehicle_number', 'state', 'city',
    'driver_phone', 'owner_phone',
    'loading_address', 'unloading_address',
    'total_booking', 'payment_1', 'payment_2', 'payment_3',
]


def export_to_excel(trips, dest_dir=None):
    if dest_dir is None:
        dest_dir = os.path.expanduser('~/Desktop')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'TripLog'

    header_fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
    header_font = Font(color='FFFFFF', bold=True)

    for col, header in enumerate(HEADERS, start=1):
        cell = ws.cell(row=1, column=col, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')

    for row_idx, trip in enumerate(trips, start=2):
        # Columns 1–12: direct fields
        for col_idx, field in enumerate(FIELD_MAP, start=1):
            ws.cell(row=row_idx, column=col_idx, value=trip.get(field, ''))

        # Column 13: Material
        ws.cell(row=row_idx, column=13, value=trip.get('material', ''))

        # Column 14: Weight (T) — convert kg → tonnes
        weight_kg = trip.get('material_weight', 0) or 0
        ws.cell(row=row_idx, column=14, value=round(weight_kg / 1000, 3))

        # Columns 15–17: computed
        p1 = trip.get('payment_1', 0) or 0
        p2 = trip.get('payment_2', 0) or 0
        p3 = trip.get('payment_3', 0) or 0
        total = trip.get('total_booking', 0) or 0
        received = calc_received(p1, p2, p3)
        pending = calc_pending(total, p1, p2, p3)
        status = calc_status(pending, p1, p2, p3)

        ws.cell(row=row_idx, column=15, value=received)
        ws.cell(row=row_idx, column=16, value=pending)
        ws.cell(row=row_idx, column=17, value=status)

    for col in ws.columns:
        max_len = max((len(str(cell.value or '')) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

    filename = f'TripLog_Export_{date.today().isoformat()}.xlsx'
    out_path = os.path.join(dest_dir, filename)
    wb.save(out_path)
    return out_path
```

- [ ] **Step 4: Run all export tests**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -m pytest tests/test_export.py -v
```

Expected: All 6 tests PASS (4 existing + 2 new).

- [ ] **Step 5: Commit**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
git add export.py tests/test_export.py
git commit -m "feat: add Material and Weight (T) columns to Excel export"
```

---

## Task 4: NiceGUI frontend — form fields and table column

**Files:**
- Modify: `ui/trips.py`

- [ ] **Step 1: Add Material & Weight columns to the table definition**

In `ui/trips.py`, find the `COLUMNS` list at the top. Add two new columns after `state_city`:

```python
COLUMNS = [
    {'name': 'date',            'label': 'Date',          'field': 'date',            'sortable': True},
    {'name': 'vehicle_number',  'label': 'Vehicle No.',   'field': 'vehicle_number',  'sortable': True},
    {'name': 'route',           'label': 'From → To',     'field': 'route'},
    {'name': 'state_city',      'label': 'State / City',  'field': 'state_city'},
    {'name': 'material',        'label': 'Material',      'field': 'material'},
    {'name': 'weight_t',        'label': 'Weight (T)',    'field': 'weight_t'},
    {'name': 'total_booking',   'label': 'Booking ₹',    'field': 'total_booking',   'sortable': True},
    {'name': 'received',        'label': 'Received ₹',   'field': 'received',        'sortable': True},
    {'name': 'status',          'label': 'Status',        'field': 'status'},
    {'name': 'actions',         'label': 'Actions',       'field': 'actions'},
]
```

- [ ] **Step 2: Add weight_t to `_build_row`**

Find the `_build_row` function. Add the `weight_t` computed field (kg ÷ 1000):

```python
def _build_row(trip: dict) -> dict:
    p1, p2, p3 = trip['payment_1'], trip['payment_2'], trip['payment_3']
    pending = calc_pending(trip['total_booking'], p1, p2, p3)
    received = calc_received(p1, p2, p3)
    weight_kg = trip.get('material_weight', 0) or 0
    return {
        **trip,
        'route':      f"{trip['loading_address']} → {trip['unloading_address']}",
        'state_city': f"{trip['state']} / {trip['city']}",
        'received':   received,
        'pending':    pending,
        'status':     calc_status(pending, p1, p2, p3),
        'weight_t':   f"{weight_kg / 1000:.2f} T" if weight_kg else '—',
    }
```

- [ ] **Step 3: Add form fields for Material and Weight in `_open_modal`**

Inside `_open_modal`, find the Route section block (the `_section_box('directions_car', 'Trip Details')` context — note: loading/unloading addresses are in this box). After the loading/unloading row, add a new row with Material and Weight fields:

Find this block:
```python
                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%; margin-top: 12px;'):
                        f_loading = _field('Loading Address *',   trip, 'loading_address',  'text', 'Pickup location')
                        f_unload  = _field('Unloading Address *', trip, 'unloading_address','text', 'Delivery location')
```

Add immediately after it (still inside the `_section_box` context):

```python
                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%; margin-top: 12px;'):
                        f_material        = _field('Material',      trip, 'material',        'text',   'e.g. Cotton Bales, Steel Rods')
                        f_material_weight = _field('Weight (kg)',   trip, 'material_weight', 'number', 'Weight of cargo in kg')
```

- [ ] **Step 4: Update `_save` to include the new fields**

Find the `_save` function. Add `material` and `material_weight` to the `kwargs` dict:

```python
        kwargs = dict(
            date=f_date.value,
            vehicle_number=f_vehicle.value.strip().upper(),
            state=(f_state.value or '').strip(),
            city=(f_city.value or '').strip(),
            driver_phone=f_driver.value.strip() if f_driver.value else '',
            owner_phone=f_owner.value.strip() if f_owner.value else '',
            loading_address=f_loading.value.strip(),
            unloading_address=f_unload.value.strip(),
            total_booking=float(f_total.value),
            payment_1=float(f_p1.value or 0),
            payment_2=float(f_p2.value or 0),
            payment_3=float(f_p3.value or 0),
            payment_1_image=image_state[1],
            payment_2_image=image_state[2],
            payment_3_image=image_state[3],
            party_name=f_party_name.value.strip() if f_party_name.value else '',
            party_contact=f_party_contact.value.strip() if f_party_contact.value else '',
            material=f_material.value.strip() if f_material.value else '',
            material_weight=float(f_material_weight.value or 0),
        )
```

- [ ] **Step 5: Verify the NiceGUI app imports cleanly**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -c "from ui import trips; print('NiceGUI trips.py OK')"
```

Expected output: `NiceGUI trips.py OK`

- [ ] **Step 6: Commit**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
git add ui/trips.py
git commit -m "feat: add Material and Weight fields to NiceGUI trip form and table"
```

---

## Task 5: React frontend — form fields and table column

**Files:**
- Modify: `frontend/src/components/TripModal.jsx`
- Modify: `frontend/src/pages/TripsPage.jsx`

### TripModal.jsx

- [ ] **Step 1: Add fields to `EMPTY_FORM`**

Find `EMPTY_FORM` and add two new properties:

```javascript
const EMPTY_FORM = {
  date: new Date().toISOString().slice(0, 10),
  vehicle_number: '',
  state: '',
  city: '',
  driver_phone: '',
  owner_phone: '',
  party_name: '',
  party_contact: '',
  loading_address: '',
  unloading_address: '',
  material: '',
  material_weight: '',
  total_booking: '',
  payment_1: '',
  payment_2: '',
  payment_3: '',
  note: '',
}
```

- [ ] **Step 2: Populate form from trip on edit**

In the `useEffect` that loads a trip (inside the `if (tripId)` branch), add the new fields to `setForm(...)`:

```javascript
        setForm({
          date: t.date || EMPTY_FORM.date,
          vehicle_number: t.vehicle_number || '',
          state: t.state || '',
          city: t.city || '',
          driver_phone: t.driver_phone || '',
          owner_phone: t.owner_phone || '',
          party_name: t.party_name || '',
          party_contact: t.party_contact || '',
          loading_address: t.loading_address || '',
          unloading_address: t.unloading_address || '',
          material: t.material || '',
          material_weight: t.material_weight?.toString() || '',
          total_booking: t.total_booking?.toString() || '',
          payment_1: t.payment_1?.toString() || '',
          payment_2: t.payment_2?.toString() || '',
          payment_3: t.payment_3?.toString() || '',
          note: t.note || '',
        })
```

- [ ] **Step 3: Include fields in `handleSave` payload**

Find the `data` object in `handleSave`. Add the two new fields:

```javascript
      const data = {
        date: form.date,
        vehicle_number: form.vehicle_number.toUpperCase(),
        state: form.state,
        city: form.city,
        driver_phone: form.driver_phone,
        owner_phone: form.owner_phone,
        party_name: form.party_name,
        party_contact: form.party_contact,
        note: form.note,
        loading_address: form.loading_address,
        unloading_address: form.unloading_address,
        material: form.material,
        material_weight: parseFloat(form.material_weight) || 0,
        total_booking: parseFloat(form.total_booking) || 0,
        payment_1: parseFloat(form.payment_1) || 0,
        payment_2: parseFloat(form.payment_2) || 0,
        payment_3: parseFloat(form.payment_3) || 0,
        payment_1_image: trip?.payment_1_image || null,
        payment_2_image: trip?.payment_2_image || null,
        payment_3_image: trip?.payment_3_image || null,
      }
```

- [ ] **Step 4: Add form fields to the Route section**

Find the Route section (the `bg-orange-50` div). After the existing `grid grid-cols-2` div containing From/To inputs, add a new grid row for Material and Weight:

```jsx
          {/* Route */}
          <div className="bg-orange-50 rounded-xl p-5">
            <SectionHeader icon={MapPin} title="Route" />
            <div className="grid grid-cols-2 gap-4">
              <Field label="From (Loading Point)" required>
                <input
                  type="text"
                  value={form.loading_address}
                  onChange={set('loading_address')}
                  placeholder="e.g. Surat Textile Market"
                  className={inputCls}
                />
              </Field>
              <Field label="To (Unloading Point)" required>
                <input
                  type="text"
                  value={form.unloading_address}
                  onChange={set('unloading_address')}
                  placeholder="e.g. Mumbai APMC Yard"
                  className={inputCls}
                />
              </Field>
              <Field label="Material">
                <input
                  type="text"
                  value={form.material}
                  onChange={set('material')}
                  placeholder="e.g. Cotton Bales, Steel Rods"
                  className={inputCls}
                />
              </Field>
              <Field label="Weight (kg)">
                <div className="relative">
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    value={form.material_weight}
                    onChange={set('material_weight')}
                    onKeyDown={blockNonNumeric}
                    placeholder="0"
                    className={inputCls + ' pr-20'}
                  />
                  {form.material_weight && parseFloat(form.material_weight) > 0 && (
                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-gray-400 font-medium pointer-events-none">
                      = {(parseFloat(form.material_weight) / 1000).toFixed(2)} T
                    </span>
                  )}
                </div>
              </Field>
            </div>
          </div>
```

### TripsPage.jsx

- [ ] **Step 5: Add Material and Weight columns to the table header**

Find the `<thead>` row in `TripsPage.jsx`. Add `'Material'` and `'Weight (T)'` to the columns array:

```jsx
                <tr className="bg-gray-50 border-b border-gray-200">
                  {['Date', 'Vehicle #', 'From → To', 'Material', 'Weight (T)', 'Booking', 'Received', 'Pending', 'Status', ''].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-bold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                  ))}
                </tr>
```

- [ ] **Step 6: Add Material and Weight cells to the table body**

Find the `<tbody>` rows section. The `<td>` cells are rendered for each trip `t`. After the `From → To` cell (the third `<td>` with the blue/green dot layout) and before the Booking `<td>`, add:

```jsx
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {t.material || <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3 text-gray-600 whitespace-nowrap">
                      {t.material_weight
                        ? `${(t.material_weight / 1000).toFixed(2)} T`
                        : <span className="text-gray-300">—</span>
                      }
                    </td>
```

- [ ] **Step 7: Rebuild the frontend**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog/frontend
npm run build
```

Expected: Build completes with no errors.

- [ ] **Step 8: Commit**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
git add frontend/src/components/TripModal.jsx frontend/src/pages/TripsPage.jsx frontend/dist
git commit -m "feat: add Material and Weight fields to React trip form and table"
```

---

## Task 6: Full regression — run all tests

- [ ] **Step 1: Run the full test suite**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -m pytest tests/ -v
```

Expected: All tests PASS (no failures, no errors).

- [ ] **Step 2: Verify export column count is correct**

```bash
cd /Users/sagarkoshti/PyCharmMiscProject/triplog
python -c "
from export import HEADERS
print('Column count:', len(HEADERS))
print('Columns:', HEADERS)
"
```

Expected output:
```
Column count: 17
Columns: ['Date', 'Vehicle Number', 'State', 'City', 'Driver Phone', 'Owner Phone', 'Loading Address', 'Unloading Address', 'Total Booking (₹)', 'Payment 1 (₹)', 'Payment 2 (₹)', 'Payment 3 (₹)', 'Material', 'Weight (T)', 'Received (₹)', 'Pending (₹)', 'Status']
```