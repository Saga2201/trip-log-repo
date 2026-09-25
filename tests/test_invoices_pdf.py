import pytest
import database
from backend.pdf.generator import render_pdf, render_all_zip
from backend.pdf.filters import inr_words, format_inr


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(database, 'DB_PATH', str(tmp_path / 'test.db'))
    database.init_db()


def test_pdf_module_imports():
    import backend.pdf                        # noqa: F401
    from backend.pdf.company import COMPANY

    assert COMPANY["name"] == "JB Transports"
    assert isinstance(COMPANY["phones"], list)
    assert len(COMPANY["phones"]) >= 1
    assert "contact_person" not in COMPANY  # removed per user request


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
    result = inr_words(24000)
    assert "Twenty" in result and "Thousand" in result
    assert result.startswith("Rupees") and result.endswith("Only")


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


def test_party_bill_pdf_contains_key_fields():
    inv = _seed_invoice()
    text = _pdf_text(render_pdf("party_bill", inv))
    assert inv["serial_number"] in text
    assert "Coal King Biogene" in text
    assert "24,000" in text                  # total
    assert "Twenty-Four Thousand" in text    # amount in words
    assert "24DKCPP6873H2ZS" in text         # GST from company
