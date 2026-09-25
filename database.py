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
        if 'party_rate' not in existing:
            conn.execute('ALTER TABLE trips ADD COLUMN party_rate REAL DEFAULT 0')
        # ── invoices ─────────────────────────────────────────────────────
        conn.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT NOT NULL UNIQUE,
                date TEXT NOT NULL,
                vehicle_number TEXT NOT NULL,
                mobile1 TEXT DEFAULT '',
                mobile2 TEXT DEFAULT '',
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
        # Additive column migrations for existing invoices tables.
        existing_inv = {row[1] for row in conn.execute('PRAGMA table_info(invoices)')}
        for col in ('mobile1', 'mobile2'):
            if col not in existing_inv:
                conn.execute(f"ALTER TABLE invoices ADD COLUMN {col} TEXT DEFAULT ''")
        conn.commit()


def add_trip(date, vehicle_number, state, city, driver_phone, owner_phone,
             loading_address, unloading_address, total_booking,
             payment_1=0.0, payment_2=0.0, payment_3=0.0,
             payment_1_image=None, payment_2_image=None, payment_3_image=None,
             party_name='', party_contact='', note='',
             material='', material_weight=0.0, party_rate=0.0):
    with _get_conn() as conn:
        cursor = conn.execute('''
            INSERT INTO trips (date, vehicle_number, state, city, driver_phone, owner_phone,
                loading_address, unloading_address, total_booking,
                payment_1, payment_2, payment_3, created_at,
                payment_1_image, payment_2_image, payment_3_image,
                party_name, party_contact, note,
                material, material_weight, party_rate)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, vehicle_number, state, city, driver_phone, owner_phone,
              loading_address, unloading_address, total_booking,
              payment_1, payment_2, payment_3, datetime.now().isoformat(),
              payment_1_image, payment_2_image, payment_3_image,
              party_name, party_contact, note,
              material, material_weight, party_rate))
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
                material='', material_weight=0.0, party_rate=0.0):
    with _get_conn() as conn:
        conn.execute('''
            UPDATE trips SET date=?, vehicle_number=?, state=?, city=?,
                driver_phone=?, owner_phone=?, loading_address=?,
                unloading_address=?, total_booking=?,
                payment_1=?, payment_2=?, payment_3=?,
                payment_1_image=?, payment_2_image=?, payment_3_image=?,
                party_name=?, party_contact=?, note=?,
                material=?, material_weight=?, party_rate=?
            WHERE id=?
        ''', (date, vehicle_number, state, city, driver_phone, owner_phone,
              loading_address, unloading_address, total_booking,
              payment_1, payment_2, payment_3,
              payment_1_image, payment_2_image, payment_3_image,
              party_name, party_contact, note,
              material, material_weight, party_rate,
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


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------
from typing import List, Optional, Tuple

_INVOICE_COLS = [
    "date", "vehicle_number",
    "mobile1", "mobile2",
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
]

_NUMERIC_COLS = {
    "lr_packages",
    "lr_weight_nett", "lr_weight_charged", "lr_rate",
    "lr_service_tax", "lr_st_charge", "lr_less_advance",
    "lr_insurance_amount", "lr_ref_value",
    "pb_freight", "pb_hamali", "pb_halting",
    "db_fare", "db_advance", "db_collection",
    "db_previous_balance", "db_advance_deposited",
}


def _enrich_invoice(row: dict) -> dict:
    """Add computed totals to an invoice dict."""
    lr_freight = (row.get("lr_weight_charged") or 0) * (row.get("lr_rate") or 0)
    lr_final = lr_freight + (row.get("lr_service_tax") or 0) + (row.get("lr_st_charge") or 0) - (row.get("lr_less_advance") or 0)
    pb_total = (row.get("pb_freight") or 0) + (row.get("pb_hamali") or 0) + (row.get("pb_halting") or 0)
    db_balance = (row.get("db_fare") or 0) - (row.get("db_advance") or 0)
    return {
        **row,
        "lr_freight_total": lr_freight,
        "lr_final_total": lr_final,
        "pb_amount_total": pb_total,
        "db_balance_fare": db_balance,
    }


_GLOBAL_SEQ_KEY = "global"


def _allocate_serial(conn, date_str: str) -> str:
    """Allocate and reserve the next simple auto-incrementing serial.
    Returns str(n) starting at "1" and incrementing forever.
    Called from within a transaction; sqlite3 opens BEGIN implicitly."""
    conn.execute(
        "INSERT INTO invoice_sequences (financial_year, last_seq) VALUES (?, 0) "
        "ON CONFLICT(financial_year) DO NOTHING",
        (_GLOBAL_SEQ_KEY,),
    )
    conn.execute(
        "UPDATE invoice_sequences SET last_seq = last_seq + 1 WHERE financial_year = ?",
        (_GLOBAL_SEQ_KEY,),
    )
    row = conn.execute(
        "SELECT last_seq FROM invoice_sequences WHERE financial_year = ?",
        (_GLOBAL_SEQ_KEY,),
    ).fetchone()
    return str(row[0])


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


def preview_next_serial(date_str: str) -> str:
    """Peek what the NEXT serial would be, without reserving. date_str is ignored
    (kept in the signature for API compatibility with the old FY-scoped version)."""
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT last_seq FROM invoice_sequences WHERE financial_year = ?",
            (_GLOBAL_SEQ_KEY,),
        ).fetchone()
        next_seq = (row[0] if row else 0) + 1
    return str(next_seq)