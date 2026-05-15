import os
import pytest
import database


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.db'))
    database.init_db()


def test_add_and_get_all_trips():
    trip_id = database.add_trip(
        date='2026-05-15',
        vehicle_number='GJ 12 AB 1234',
        state='Gujarat',
        city='Surat',
        driver_phone='9876543210',
        owner_phone='9123456789',
        loading_address='Surat Textile Market',
        unloading_address='Mumbai Warehouse',
        total_booking=18000.0,
        payment_1=10000.0,
        payment_2=5000.0,
        payment_3=0.0,
    )
    assert trip_id == 1
    trips = database.get_all_trips()
    assert len(trips) == 1
    assert trips[0]['vehicle_number'] == 'GJ 12 AB 1234'
    assert trips[0]['total_booking'] == 18000.0


def test_get_trip_by_id():
    database.add_trip(
        date='2026-05-14', vehicle_number='MH 04 XY 5678',
        state='Maharashtra', city='Pune',
        driver_phone='', owner_phone='',
        loading_address='Pune Station', unloading_address='Delhi Hub',
        total_booking=32000.0, payment_1=20000.0, payment_2=0.0, payment_3=0.0,
    )
    trip = database.get_trip_by_id(1)
    assert trip['vehicle_number'] == 'MH 04 XY 5678'


def test_get_trip_by_id_missing_returns_none():
    assert database.get_trip_by_id(999) is None


def test_update_trip():
    database.add_trip(
        date='2026-05-10', vehicle_number='RJ 14 CD 9012',
        state='Rajasthan', city='Jaipur',
        driver_phone='', owner_phone='',
        loading_address='Jaipur Market', unloading_address='Ahmedabad Port',
        total_booking=12500.0, payment_1=0.0, payment_2=0.0, payment_3=0.0,
    )
    database.update_trip(
        trip_id=1, date='2026-05-10', vehicle_number='RJ 14 CD 9012',
        state='Rajasthan', city='Jaipur',
        driver_phone='9000000001', owner_phone='',
        loading_address='Jaipur Market', unloading_address='Ahmedabad Port',
        total_booking=12500.0, payment_1=6000.0, payment_2=0.0, payment_3=0.0,
    )
    trip = database.get_trip_by_id(1)
    assert trip['payment_1'] == 6000.0
    assert trip['driver_phone'] == '9000000001'


def test_delete_trip():
    database.add_trip(
        date='2026-05-01', vehicle_number='GJ 01 EF 3456',
        state='Gujarat', city='Rajkot',
        driver_phone='', owner_phone='',
        loading_address='Rajkot APMC', unloading_address='Hyderabad Market',
        total_booking=22000.0, payment_1=22000.0, payment_2=0.0, payment_3=0.0,
    )
    database.delete_trip(1)
    assert database.get_all_trips() == []
