import re
import uuid
from pathlib import Path
from nicegui import ui
import database
from helpers import calc_pending, calc_received, calc_status
from ui.components import sidebar, PAGE_BG
from locations import STATES_CITIES, ALL_STATES

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


def _summary(all_rows):
    from datetime import date
    month = date.today().strftime('%Y-%m')
    total_booking = sum(r['total_booking'] for r in all_rows)
    total_pending = sum(r['pending'] for r in all_rows)
    this_month    = sum(r['total_booking'] for r in all_rows if r['date'].startswith(month))
    return len(all_rows), total_booking, total_pending, this_month


def trips_page(open_new: bool = False):
    sidebar('trips')

    with ui.element('div').style(
        'width: 100%; padding: 24px; box-sizing: border-box; flex: 1; '
        'display: flex; flex-direction: column; gap: 0;'
    ):
        all_trips = [_build_row(t) for t in database.get_all_trips()]
        count, total_booking, total_pending, this_month = _summary(all_trips)

        # ── Summary cards ──────────────────────────────────────────────
        with ui.row().style('gap: 16px; margin-bottom: 20px; flex-wrap: wrap; width: 100%;'):
            _card('Total Trips',      str(count),              '#1e3a5f')
            _card('Total Booking',    f'₹{total_booking:,.0f}','#2e7d32')
            _card('Pending Payment',  f'₹{total_pending:,.0f}','#e53935')
            _card('This Month',       f'₹{this_month:,.0f}',   '#f57c00')

        # ── Search + New Trip button ────────────────────────────────────
        with ui.row().style('gap: 12px; margin-bottom: 16px; align-items: center; width: 100%;'):
            search_input = ui.input(placeholder='🔍  Search by vehicle, city, state...').style(
                'flex: 1; border: 1px solid #dce6f0; border-radius: 6px; '
                'background: #fff; font-size: 13px;'
            )
            ui.button('+ New Trip', on_click=lambda: _open_modal(None, refresh)).style(
                'background-color: #1e3a5f; color: #fff; border-radius: 6px; padding: 8px 18px;'
            )

        # ── Table ──────────────────────────────────────────────────────
        table_rows = list(all_trips)
        table = ui.table(columns=COLUMNS, rows=table_rows, row_key='id').style(
            'background: #fff; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.08); '
            'width: 100%; flex: 1; min-width: 0;'
        ).props('flat')

        table.add_slot('body-cell-status', '''
            <q-td :props="props">
                <span :style="props.row.status === 'Paid'
                    ? 'background-color:#e8f5e9;color:#2e7d32;border-radius:12px;padding:2px 10px;font-size:11px;font-weight:600;'
                    : props.row.status === 'Partial'
                    ? 'background-color:#fff3e0;color:#f57c00;border-radius:12px;padding:2px 10px;font-size:11px;font-weight:600;'
                    : 'background-color:#ffebee;color:#e53935;border-radius:12px;padding:2px 10px;font-size:11px;font-weight:600;'">
                    {{ props.row.status }}
                </span>
            </q-td>
        ''')
        table.add_slot('body-cell-actions', r'''
            <q-td :props="props">
                <q-btn flat dense icon="edit" color="primary"
                    @click.stop="$parent.$emit('edit', props.row)" />
                <q-btn flat dense icon="delete" color="negative"
                    @click.stop="$parent.$emit('delete', props.row)" />
            </q-td>
        ''')

        row_count = ui.label(f'Showing {len(table_rows)} trips').style('color: #888; font-size: 11px; margin-top: 6px;')

        # Wire search filter
        def _filter(e):
            q = e.value.lower().strip()
            filtered = [r for r in all_trips if not q or
                        q in r['vehicle_number'].lower() or
                        q in r['state'].lower() or
                        q in r['city'].lower()]
            table.rows = filtered
            row_count.text = f'Showing {len(filtered)} trips'

        search_input.on('input', _filter)

        # Wire edit/delete events
        def refresh():
            ui.navigate.to('/')

        def _handle_edit(e):
            try:
                args = e.args
                if isinstance(args, list):
                    args = args[0]
                trip_id = args.get('id') if isinstance(args, dict) else int(args)
                if trip_id:
                    _open_modal(trip_id, refresh)
            except Exception:
                ui.notify('Could not open editor', type='negative')

        def _handle_delete(e):
            try:
                args = e.args
                if isinstance(args, list):
                    args = args[0]
                trip_id = args.get('id') if isinstance(args, dict) else int(args)
                if trip_id:
                    _confirm_delete(trip_id, refresh)
            except Exception:
                ui.notify('Could not delete trip', type='negative')

        table.on('edit', _handle_edit)
        table.on('delete', _handle_delete)

    if open_new:
        _open_modal(None, refresh)


def _card(title: str, value: str, accent: str):
    with ui.card().style(
        f'flex: 1; min-width: 160px; border-left: 4px solid {accent}; '
        'padding: 12px 16px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.07);'
    ):
        ui.label(title).style('color: #888; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;')
        ui.label(value).style(f'color: {accent}; font-size: 22px; font-weight: 700; margin-top: 4px;')


def _open_modal(trip_id, on_save):
    trip = database.get_trip_by_id(trip_id) if trip_id else None
    is_edit = bool(trip)

    # ── State for city linkage ─────────────────────────────────────────
    init_state = (trip.get('state') or '') if trip else ''
    init_city  = (trip.get('city')  or '') if trip else ''
    city_opts  = STATES_CITIES.get(init_state, [])

    # image_state[n] = current image file path or None
    image_state = {
        1: trip.get('payment_1_image') if trip else None,
        2: trip.get('payment_2_image') if trip else None,
        3: trip.get('payment_3_image') if trip else None,
    }

    # ── Callbacks defined before any UI references them ────────────────
    def _on_state_change(e):
        chosen = e.value or ''
        cities = STATES_CITIES.get(chosen, [])
        f_city.options = cities
        f_city.value = None
        f_city.update()

    def _update_pending(_=None):
        try:
            total   = float(f_total.value or 0)
            pending = calc_pending(total,
                                   float(f_p1.value or 0),
                                   float(f_p2.value or 0),
                                   float(f_p3.value or 0))
            received = total - pending
            pending_label.set_text(
                f'Received  ₹{received:,.0f}   •   Pending  ₹{pending:,.0f}'
            )
            pending_label.style(
                'background: #e8f5e9; color: #2e7d32;' if pending <= 0
                else 'background: #fff3e0; color: #e65100;'
            )
        except (ValueError, TypeError):
            pending_label.set_text('Enter amounts above to calculate pending')
            pending_label.style('background: #f5f5f5; color: #9e9e9e;')

    def _save():
        errors = _validate(
            f_date.value, f_vehicle.value,
            f_state.value or '', f_city.value or '',
            f_driver.value, f_owner.value,
            f_loading.value, f_unload.value,
            f_total.value, f_p1.value, f_p2.value, f_p3.value,
            f_party_contact.value,
        )
        if errors:
            ui.notify(errors[0], type='negative', position='top')
            return
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
        if is_edit:
            database.update_trip(trip['id'], **kwargs)
            ui.notify('Trip updated', type='positive', position='top')
        else:
            database.add_trip(**kwargs)
            ui.notify('Trip saved', type='positive', position='top')
        dialog.close()
        on_save()

    # ── Dialog ─────────────────────────────────────────────────────────
    # The card is forced into a flex column with stretch so every child row
    # fills the full card width reliably across Quasar versions.
    with ui.dialog() as dialog, ui.card().style(
        'width: 960px; max-width: 97vw; padding: 0; overflow: hidden; '
        'display: flex; flex-direction: column; align-items: stretch; gap: 0;'
    ):
        # ── Header ────────────────────────────────────────────────────
        with ui.row().style(
            'background: #1e3a5f; padding: 14px 22px; width: 100%; box-sizing: border-box; '
            'align-items: center; justify-content: space-between; flex-wrap: nowrap;'
        ):
            with ui.row().style('align-items: center; gap: 12px; flex-wrap: nowrap;'):
                ui.icon('edit_road' if is_edit else 'local_shipping').style(
                    'color: #4fc3f7; font-size: 26px; flex-shrink: 0;'
                )
                with ui.column().style('gap: 2px;'):
                    ui.label('Edit Trip' if is_edit else 'New Trip').style(
                        'color: #fff; font-size: 17px; font-weight: 700; line-height: 1.2;'
                    )
                    ui.label(
                        f"Trip #{trip['id']}  ·  {trip['vehicle_number']}" if is_edit
                        else 'Enter trip details, payments and receipt photos'
                    ).style('color: #90caf9; font-size: 11px;')
            ui.button(icon='close', on_click=dialog.close).props('flat round dense').style(
                'color: rgba(255,255,255,0.75); flex-shrink: 0;'
            )

        # ── Scrollable body ────────────────────────────────────────────
        with ui.scroll_area().style('flex: 1; max-height: 74vh; width: 100%;'):
            with ui.column().style(
                'padding: 22px; gap: 16px; width: 100%; box-sizing: border-box;'
            ):

                # ── Trip Details ──────────────────────────────────────
                with _section_box('directions_car', 'Trip Details'):
                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%;'):
                        f_date    = _field('Date *',           trip, 'date',           'date', '')
                        f_vehicle = _field('Vehicle Number *', trip, 'vehicle_number', 'text', 'e.g. GJ 12 AB 1234')

                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%; margin-top: 12px;'):
                        f_state = ui.select(
                            options=ALL_STATES,
                            label='State',
                            value=init_state or None,
                            with_input=True,
                            clearable=True,
                            on_change=_on_state_change,
                        ).style('min-width: 220px; flex: 1;').props('outlined dense')

                        f_city = ui.select(
                            options=city_opts,
                            label='City',
                            value=init_city if init_city in city_opts else (init_city or None),
                            with_input=True,
                            clearable=True,
                            new_value_mode='add',
                        ).style('min-width: 220px; flex: 1;').props('outlined dense')

                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%; margin-top: 12px;'):
                        f_loading = _field('Loading Address *',   trip, 'loading_address',  'text', 'Pickup location')
                        f_unload  = _field('Unloading Address *', trip, 'unloading_address','text', 'Delivery location')

                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%; margin-top: 12px;'):
                        f_material        = _field('Material',    trip, 'material',        'text',   'e.g. Cotton Bales, Steel Rods')
                        f_material_weight = _field('Weight (kg)', trip, 'material_weight', 'number', 'Weight of cargo in kg')

                # ── Contact Details ───────────────────────────────────
                with _section_box('contacts', 'Contact Details'):
                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%;'):
                        f_driver = _field('Driver Phone', trip, 'driver_phone', 'text', '10 digits only')
                        f_owner  = _field('Owner Phone',  trip, 'owner_phone',  'text', '10 digits only')
                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%; margin-top: 12px;'):
                        f_party_name    = _field('Party Name',    trip, 'party_name',    'text', 'Party / consignee name')
                        f_party_contact = _field('Party Contact', trip, 'party_contact', 'text', '10 digits only')

                # ── Payment Details ───────────────────────────────────
                with _section_box('currency_rupee', 'Payment Details'):
                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%;'):
                        f_total = _field('Total Booking ₹ *', trip, 'total_booking', 'number', 'Full booking amount')

                    with ui.row().style('align-items: center; gap: 8px; margin: 16px 0 10px;'):
                        ui.separator().style('flex: 1;')
                        ui.label('Instalments & Receipts').style(
                            'font-size: 10px; font-weight: 700; color: #90a4ae; '
                            'text-transform: uppercase; letter-spacing: 0.8px; white-space: nowrap;'
                        )
                        ui.separator().style('flex: 1;')

                    with ui.row().style('gap: 14px; flex-wrap: wrap; width: 100%; align-items: flex-start;'):
                        f_p1 = _payment_card('Payment 1 ₹', trip, 'payment_1', 1, image_state)
                        f_p2 = _payment_card('Payment 2 ₹', trip, 'payment_2', 2, image_state)
                        f_p3 = _payment_card('Payment 3 ₹', trip, 'payment_3', 3, image_state)

                    pending_label = ui.label('Enter amounts above to calculate pending').style(
                        'background: #f5f5f5; color: #9e9e9e; border-radius: 8px; '
                        'padding: 10px 16px; width: 100%; margin-top: 10px; '
                        'font-size: 13px; font-weight: 600; box-sizing: border-box;'
                    )
                    for fld in (f_total, f_p1, f_p2, f_p3):
                        fld.on('input', _update_pending)
                    _update_pending()

        # ── Footer ────────────────────────────────────────────────────
        with ui.row().style(
            'padding: 12px 22px; border-top: 1px solid #e8eef4; background: #f8faff; '
            'justify-content: flex-end; gap: 10px; width: 100%; box-sizing: border-box; flex-wrap: nowrap;'
        ):
            ui.button('Cancel', on_click=dialog.close).props('flat').style(
                'color: #546e7a; font-weight: 600;'
            )
            ui.button('Save Trip', on_click=_save).props('icon=save unelevated').style(
                'background: #1e3a5f; color: #fff; border-radius: 8px; '
                'padding: 6px 22px; font-weight: 600; font-size: 13px;'
            )

    dialog.open()


from contextlib import contextmanager


@contextmanager
def _section_box(icon_name: str, title: str):
    """Renders a titled section card for the modal."""
    with ui.element('div').style(
        'border: 1px solid #e8eef4; border-radius: 10px; padding: 16px; '
        'background: #fafcff; width: 100%; box-sizing: border-box;'
    ):
        with ui.row().style('align-items: center; gap: 8px; margin-bottom: 12px;'):
            ui.icon(icon_name).style('color: #1e3a5f; font-size: 18px;')
            ui.label(title).style(
                'font-size: 12px; font-weight: 700; color: #1e3a5f; '
                'text-transform: uppercase; letter-spacing: 0.8px;'
            )
        yield


def _field(label: str, trip, field: str, input_type: str, hint: str = ''):
    value = str(trip[field]) if trip and trip.get(field) is not None else ''
    inp = ui.input(label=label, value=value).style('min-width: 180px; flex: 1;').props('outlined dense')
    if input_type == 'date':
        inp.props('type=date')
    if hint:
        inp.props(f'hint="{hint}"')
    return inp


def _payment_card(label: str, trip, field: str, n: int, image_state: dict) -> ui.input:
    """Payment amount input + receipt image upload in a card."""
    amount_val = str(trip[field]) if trip and trip.get(field) is not None else ''
    current_img = [image_state.get(n)]  # mutable ref via list

    # ── All callbacks defined first to avoid UnboundLocalError ────────
    def _on_upload(e):
        data = e.content.read()
        ext = Path(e.name).suffix.lower() or '.jpg'
        fname = f'pay_{uuid.uuid4().hex}{ext}'
        fpath = database.IMAGES_DIR / fname
        fpath.write_bytes(data)
        if current_img[0]:
            Path(current_img[0]).unlink(missing_ok=True)
        current_img[0] = str(fpath)
        image_state[n] = str(fpath)
        _render()
        ui.notify(f'Receipt {n} saved', type='positive', position='top-right')

    def _remove():
        if current_img[0]:
            Path(current_img[0]).unlink(missing_ok=True)
        current_img[0] = None
        image_state[n] = None
        _render()

    def _view_full():
        if not current_img[0]:
            return
        fname = Path(current_img[0]).name
        with ui.dialog() as dlg, ui.card().style(
            'padding: 0; background: #111; border-radius: 12px; overflow: hidden; max-width: 92vw;'
        ):
            ui.image(f'/payment_images/{fname}').style(
                'max-width: 88vw; max-height: 82vh; object-fit: contain; display: block;'
            )
            with ui.row().style(
                'justify-content: space-between; align-items: center; padding: 10px 14px; background: #111;'
            ):
                ui.label(f'Receipt — Payment {n}').style('color: #ccc; font-size: 13px;')
                ui.button('Close', icon='close', on_click=dlg.close).props('flat dense').style('color: white;')
        dlg.open()

    # ── UI ────────────────────────────────────────────────────────────
    with ui.card().style(
        'flex: 1; min-width: 200px; padding: 14px; border-radius: 10px; '
        'box-shadow: 0 1px 4px rgba(0,0,0,0.08);'
    ):
        with ui.row().style('align-items: center; gap: 6px; margin-bottom: 8px;'):
            ui.icon('payments').style('color: #2d5a8e; font-size: 16px;')
            ui.label(label).style(
                'font-size: 11px; font-weight: 700; color: #2d5a8e; '
                'text-transform: uppercase; letter-spacing: 0.5px;'
            )

        amount_inp = ui.input(placeholder='₹ Amount', value=amount_val).style('width: 100%;').props('outlined dense')

        # Hidden uploader — triggered via JS click on its native file input
        uploader = ui.upload(on_upload=_on_upload, auto_upload=True).props(
            'accept="image/*"'
        ).style('display: none; position: absolute; pointer-events: none;')
        uid = uploader.id

        img_box = ui.element('div').style('width: 100%; margin-top: 8px;')

        def _trigger():
            ui.run_javascript(
                f'document.getElementById("c{uid}")?.querySelector("input[type=file]")?.click()'
            )

        def _render():
            img_box.clear()
            with img_box:
                if current_img[0] and Path(current_img[0]).exists():
                    fname = Path(current_img[0]).name
                    ui.image(f'/payment_images/{fname}').style(
                        'width: 100%; height: 120px; object-fit: cover; '
                        'border-radius: 8px; cursor: pointer; border: 1px solid #e0e8f0;'
                    ).on('click', _view_full)
                    with ui.row().style('gap: 4px; margin-top: 6px; justify-content: space-between; width: 100%;'):
                        ui.button('View', icon='open_in_full', on_click=_view_full).props(
                            'flat dense size=xs color=primary'
                        )
                        ui.button('Replace', icon='upload', on_click=_trigger).props(
                            'flat dense size=xs color=secondary'
                        )
                        ui.button('Remove', icon='delete', on_click=_remove).props(
                            'flat dense size=xs color=negative'
                        )
                else:
                    with ui.element('div').style(
                        'border: 2px dashed #c8d8ea; border-radius: 8px; padding: 20px 8px; '
                        'text-align: center; cursor: pointer; background: #f8fbff;'
                    ).on('click', _trigger):
                        ui.icon('add_photo_alternate').style(
                            'color: #90a4ae; font-size: 36px; display: block; pointer-events: none;'
                        )
                        ui.label('Tap to add receipt photo').style(
                            'color: #607d8b; font-size: 12px; font-weight: 600; '
                            'margin-top: 6px; pointer-events: none;'
                        )
                        ui.label('JPG · PNG · PDF').style(
                            'color: #b0bec5; font-size: 10px; margin-top: 2px; pointer-events: none;'
                        )

        _render()

    return amount_inp


def _validate(date_val, vehicle_val, state_val, city_val,
              driver_val, owner_val, loading_val, unload_val,
              total_val, p1_val, p2_val, p3_val,
              party_contact_val='') -> list[str]:
    errors = []

    # Required fields
    if not date_val:
        errors.append('Date is required')
    if not vehicle_val or not vehicle_val.strip():
        errors.append('Vehicle Number is required')
    if not loading_val or not loading_val.strip():
        errors.append('Loading Address is required')
    if not unload_val or not unload_val.strip():
        errors.append('Unloading Address is required')
    if not total_val:
        errors.append('Total Booking amount is required')

    if errors:
        return errors

    # Phone validation — 10 digits if provided
    if driver_val and driver_val.strip():
        if not re.match(r'^\d{10}$', driver_val.strip()):
            errors.append('Driver phone must be exactly 10 digits (e.g. 9876543210)')
    if owner_val and owner_val.strip():
        if not re.match(r'^\d{10}$', owner_val.strip()):
            errors.append('Owner phone must be exactly 10 digits (e.g. 9876543210)')
    if party_contact_val and party_contact_val.strip():
        if not re.match(r'^\d{10}$', party_contact_val.strip()):
            errors.append('Party contact must be exactly 10 digits (e.g. 9876543210)')

    # Amount validation
    try:
        total = float(total_val)
        if total <= 0:
            errors.append('Total Booking amount must be greater than 0')
    except (ValueError, TypeError):
        errors.append('Total Booking must be a valid number')
        return errors

    try:
        p1 = float(p1_val or 0)
        p2 = float(p2_val or 0)
        p3 = float(p3_val or 0)
    except (ValueError, TypeError):
        errors.append('Payment amounts must be valid numbers')
        return errors

    if p1 < 0 or p2 < 0 or p3 < 0:
        errors.append('Payment amounts cannot be negative')
    elif p1 + p2 + p3 > total:
        errors.append(
            f'Total payments (₹{p1+p2+p3:,.0f}) cannot exceed Total Booking (₹{total:,.0f})'
        )

    return errors


def _confirm_delete(trip_id: int, on_done):
    with ui.dialog() as dlg, ui.card():
        ui.label('Delete this trip?').style('font-size: 15px; font-weight: 600; color: #e53935;')
        ui.label('This cannot be undone.').style('color: #888; margin-top: 4px;')
        with ui.row().style('justify-content: flex-end; gap: 10px; margin-top: 16px;'):
            ui.button('Cancel', on_click=dlg.close).props('flat')

            def _delete():
                database.delete_trip(trip_id)
                dlg.close()
                ui.notify('Trip deleted', type='negative')
                on_done()

            ui.button('Delete', on_click=_delete).style('background-color: #e53935; color: #fff;')
    dlg.open()
