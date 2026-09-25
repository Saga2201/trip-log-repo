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
