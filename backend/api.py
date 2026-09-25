import sys
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Make the parent triplog/ directory importable
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _parent_dir)

import database
import helpers
import export
from locations import ALL_STATES, STATES_CITIES

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(title='TripLog API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],          # allow any origin (dev only)
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
def startup():
    database.init_db()


app.mount(
    '/payment_images',
    StaticFiles(directory=str(database.IMAGES_DIR)),
    name='payment_images',
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


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
    loading_address: str
    unloading_address: str
    total_booking: float
    payment_1: float = 0.0
    payment_2: float = 0.0
    payment_3: float = 0.0
    payment_1_image: Optional[str] = None
    payment_2_image: Optional[str] = None
    payment_3_image: Optional[str] = None
    material: str = ''
    material_weight: float = 0.0
    party_rate: float = 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _enrich(trip: dict) -> dict:
    """Add computed received / pending / status / commission fields to a trip dict."""
    p1 = trip.get('payment_1') or 0.0
    p2 = trip.get('payment_2') or 0.0
    p3 = trip.get('payment_3') or 0.0
    total = trip.get('total_booking') or 0.0
    party_rate = trip.get('party_rate') or 0.0
    received = helpers.calc_received(p1, p2, p3)
    pending = helpers.calc_pending(total, p1, p2, p3)
    status = helpers.calc_status(pending, p1, p2, p3)
    commission = party_rate - total if party_rate > 0 else 0.0
    return {**trip, 'received': received, 'pending': pending, 'status': status, 'commission': commission}


def _trip_or_404(trip_id: int) -> dict:
    trip = database.get_trip_by_id(trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail=f'Trip {trip_id} not found')
    return trip


# ---------------------------------------------------------------------------
# Trip endpoints
# ---------------------------------------------------------------------------


@app.get('/trips')
def list_trips():
    trips = database.get_all_trips()
    return [_enrich(t) for t in trips]


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
        party_rate=body.party_rate,
    )
    return {'id': trip_id}


@app.get('/trips/{trip_id}')
def get_trip(trip_id: int):
    return _enrich(_trip_or_404(trip_id))


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
        party_rate=body.party_rate,
    )
    return _enrich(database.get_trip_by_id(trip_id))


@app.patch('/trips/{trip_id}/complete')
def mark_complete(trip_id: int):
    _trip_or_404(trip_id)
    database.set_completed(trip_id, True)
    return _enrich(database.get_trip_by_id(trip_id))


@app.patch('/trips/{trip_id}/reopen')
def mark_reopen(trip_id: int):
    _trip_or_404(trip_id)
    database.set_completed(trip_id, False)
    return _enrich(database.get_trip_by_id(trip_id))


@app.delete('/trips/{trip_id}', status_code=204)
def delete_trip(trip_id: int):
    _trip_or_404(trip_id)
    database.delete_trip(trip_id)


# ---------------------------------------------------------------------------
# Image endpoints
# ---------------------------------------------------------------------------


@app.post('/trips/{trip_id}/images/{n}')
async def upload_image(trip_id: int, n: int, file: UploadFile = File(...)):
    if n not in (1, 2, 3):
        raise HTTPException(status_code=400, detail='n must be 1, 2, or 3')

    trip = _trip_or_404(trip_id)
    col = f'payment_{n}_image'

    # Delete old image file if one exists
    old_path = trip.get(col)
    if old_path:
        old_file = Path(old_path)
        old_file.unlink(missing_ok=True)

    # Save new file with a UUID-based filename
    suffix = Path(file.filename).suffix if file.filename else '.jpg'
    filename = f'{uuid.uuid4()}{suffix}'
    dest = database.IMAGES_DIR / filename
    contents = await file.read()
    dest.write_bytes(contents)

    # Update the trip record with the new image path (store full path, consistent with DB schema)
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
        party_rate=trip.get('party_rate', 0.0),
    )

    return {'url': f'/payment_images/{filename}'}


@app.delete('/trips/{trip_id}/images/{n}', status_code=204)
def delete_image(trip_id: int, n: int):
    if n not in (1, 2, 3):
        raise HTTPException(status_code=400, detail='n must be 1, 2, or 3')

    trip = _trip_or_404(trip_id)
    col = f'payment_{n}_image'

    # Delete the image file
    existing_path = trip.get(col)
    if existing_path:
        Path(existing_path).unlink(missing_ok=True)

    # Clear the column in DB
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
        party_rate=trip.get('party_rate', 0.0),
    )


# ---------------------------------------------------------------------------
# Insights / Export / Locations
# ---------------------------------------------------------------------------


@app.get('/insights')
def insights():
    trips = database.get_all_trips()
    return [_enrich(t) for t in trips]


@app.get('/export')
def export_trips():
    trips = database.get_all_trips()
    # Write the xlsx to a temp directory so we can serve it
    import tempfile
    tmp_dir = tempfile.mkdtemp()
    out_path = export.export_to_excel(trips, dest_dir=tmp_dir)
    return FileResponse(
        path=out_path,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        filename=os.path.basename(out_path),
    )


@app.get('/locations')
def locations():
    return {'states': ALL_STATES, 'cities': STATES_CITIES}


# ---------------------------------------------------------------------------
# Invoices
# ---------------------------------------------------------------------------
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
