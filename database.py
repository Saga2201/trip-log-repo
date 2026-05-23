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