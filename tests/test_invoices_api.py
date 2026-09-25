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
    assert r.json() == {"serial": "1"}


def test_create_and_list(client):
    r = client.post("/invoices", json=_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] == 1
    assert body["serial_number"] == "1"

    r = client.get("/invoices")
    assert r.status_code == 200
    invoices = r.json()
    assert len(invoices) == 1
    assert invoices[0]["serial_number"] == "1"
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
