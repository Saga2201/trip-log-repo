import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trips.db')


def _get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
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
        conn.commit()


def add_trip(date, vehicle_number, state, city, driver_phone, owner_phone,
             loading_address, unloading_address, total_booking,
             payment_1=0.0, payment_2=0.0, payment_3=0.0):
    with _get_conn() as conn:
        cursor = conn.execute('''
            INSERT INTO trips (date, vehicle_number, state, city, driver_phone, owner_phone,
                loading_address, unloading_address, total_booking,
                payment_1, payment_2, payment_3, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (date, vehicle_number, state, city, driver_phone, owner_phone,
              loading_address, unloading_address, total_booking,
              payment_1, payment_2, payment_3, datetime.now().isoformat()))
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
                payment_1=0.0, payment_2=0.0, payment_3=0.0):
    with _get_conn() as conn:
        conn.execute('''
            UPDATE trips SET date=?, vehicle_number=?, state=?, city=?,
                driver_phone=?, owner_phone=?, loading_address=?,
                unloading_address=?, total_booking=?,
                payment_1=?, payment_2=?, payment_3=?
            WHERE id=?
        ''', (date, vehicle_number, state, city, driver_phone, owner_phone,
              loading_address, unloading_address, total_booking,
              payment_1, payment_2, payment_3, trip_id))
        conn.commit()


def delete_trip(trip_id):
    with _get_conn() as conn:
        conn.execute('DELETE FROM trips WHERE id = ?', (trip_id,))
        conn.commit()
