import re
from nicegui import ui
import database
from helpers import calc_pending, calc_received, calc_status
from ui.components import sidebar, PAGE_BG

COLUMNS = [
    {'name': 'date',           'label': 'Date',        'field': 'date',           'sortable': True},
    {'name': 'vehicle_number', 'label': 'Vehicle No.', 'field': 'vehicle_number', 'sortable': True},
    {'name': 'route',          'label': 'From → To',   'field': 'route'},
    {'name': 'state_city',     'label': 'State / City','field': 'state_city'},
    {'name': 'total_booking',  'label': 'Booking ₹',   'field': 'total_booking',  'sortable': True},
    {'name': 'received',       'label': 'Received ₹',  'field': 'received',       'sortable': True},
    {'name': 'status',         'label': 'Status',      'field': 'status'},
    {'name': 'actions',        'label': 'Actions',     'field': 'actions'},
]


def _build_row(trip: dict) -> dict:
    p1, p2, p3 = trip['payment_1'], trip['payment_2'], trip['payment_3']
    pending = calc_pending(trip['total_booking'], p1, p2, p3)
    received = calc_received(p1, p2, p3)
    return {
        **trip,
        'route':      f"{trip['loading_address']} → {trip['unloading_address']}",
        'state_city': f"{trip['state']} / {trip['city']}",
        'received':   received,
        'pending':    pending,
        'status':     calc_status(pending, p1, p2, p3),
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

    with ui.column().style('width: 100%; padding: 24px; box-sizing: border-box; flex: 1; gap: 0;'):
        all_trips = [_build_row(t) for t in database.get_all_trips()]
        count, total_booking, total_pending, this_month = _summary(all_trips)

        # ── Summary cards ──────────────────────────────────────────────
        with ui.row().style('gap: 16px; margin-bottom: 20px; flex-wrap: wrap;'):
            _card('Total Trips',      str(count),              '#1e3a5f')
            _card('Total Booking',    f'₹{total_booking:,.0f}','#2e7d32')
            _card('Pending Payment',  f'₹{total_pending:,.0f}','#e53935')
            _card('This Month',       f'₹{this_month:,.0f}',   '#f57c00')

        # ── Search + New Trip button ────────────────────────────────────
        with ui.row().style('gap: 12px; margin-bottom: 16px; align-items: center;'):
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
            'width: 100%; flex: 1;'
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
        table.add_slot('body-cell-actions', '''
            <q-td :props="props">
                <q-btn flat dense icon="edit" color="primary"
                    @click="$emit('edit', props.row)" />
                <q-btn flat dense icon="delete" color="negative"
                    @click="$emit('delete', props.row)" />
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

        table.on('edit', lambda e: _open_modal(e.args['id'], refresh))
        table.on('delete', lambda e: _confirm_delete(e.args['id'], refresh))

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
    title = 'Edit Trip' if trip else 'New Trip'

    with ui.dialog() as dialog, ui.card().style('width: 700px; max-width: 95vw; padding: 24px;'):
        with ui.row().style('justify-content: space-between; align-items: center; margin-bottom: 16px; width: 100%;'):
            with ui.row().style('align-items: center; gap: 8px;'):
                ui.icon('edit' if trip else 'add_circle').style('color: #1e3a5f; font-size: 22px;')
                ui.label(title).style('font-size: 16px; font-weight: 700; color: #1e3a5f;')
            ui.button(icon='close', on_click=dialog.close).props('flat round dense')

        # ── Trip Details ───────────────────────────────────────────────
        _section_label('Trip Details')
        with ui.row().style('gap: 12px; flex-wrap: wrap;'):
            f_date    = _field('Date *',             trip, 'date',             'date',   '')
            f_vehicle = _field('Vehicle Number *',   trip, 'vehicle_number',   'text',   'e.g. GJ 12 AB 1234')
            f_state   = _field('State',              trip, 'state',            'text',   'e.g. Gujarat')
            f_city    = _field('City',               trip, 'city',             'text',   'e.g. Surat')
            f_loading = _field('Loading Address *',  trip, 'loading_address',  'text',   'Pickup location')
            f_unload  = _field('Unloading Address *',trip, 'unloading_address','text',   'Delivery location')

        # ── Contact Details ────────────────────────────────────────────
        _section_label('Contact Details')
        with ui.row().style('gap: 12px; flex-wrap: wrap;'):
            f_driver = _field('Driver Phone', trip, 'driver_phone', 'text', '10 digits only')
            f_owner  = _field('Owner Phone',  trip, 'owner_phone',  'text', '10 digits only')

        # ── Payment Details ────────────────────────────────────────────
        _section_label('Payment Details')
        with ui.row().style('gap: 12px; flex-wrap: wrap;'):
            f_total = _field('Total Booking ₹ *', trip, 'total_booking', 'number', 'Full booking amount')
            f_p1    = _field('Payment 1 ₹',       trip, 'payment_1',     'number', 'First instalment')
            f_p2    = _field('Payment 2 ₹',       trip, 'payment_2',     'number', 'Second instalment')
            f_p3    = _field('Payment 3 ₹',       trip, 'payment_3',     'number', 'Third instalment')

        # Pending display
        pending_label = ui.label('').style(
            'background-color: #fff3e0; color: #e65100; border-radius: 8px; '
            'padding: 10px 16px; width: 100%; margin-top: 4px; font-weight: 600;'
        )

        def _update_pending(_=None):
            try:
                total = float(f_total.value or 0)
                p1 = float(f_p1.value or 0)
                p2 = float(f_p2.value or 0)
                p3 = float(f_p3.value or 0)
                pending = calc_pending(total, p1, p2, p3)
                pending_label.text = f'⚠️ Pending Amount: ₹{pending:,.0f}'
            except (ValueError, TypeError):
                pending_label.text = '⚠️ Pending Amount: —'

        for field in (f_total, f_p1, f_p2, f_p3):
            field.on('input', _update_pending)
        _update_pending()

        # ── Actions ────────────────────────────────────────────────────
        with ui.row().style('justify-content: flex-end; gap: 10px; margin-top: 16px;'):
            ui.button('Cancel', on_click=dialog.close).props('flat')

            def _save():
                errors = _validate(
                    f_date.value, f_vehicle.value, f_state.value, f_city.value,
                    f_driver.value, f_owner.value, f_loading.value, f_unload.value,
                    f_total.value, f_p1.value, f_p2.value, f_p3.value,
                )
                if errors:
                    ui.notify(errors[0], type='negative')
                    return
                kwargs = dict(
                    date=f_date.value,
                    vehicle_number=f_vehicle.value.strip().upper(),
                    state=f_state.value.strip() if f_state.value else '',
                    city=f_city.value.strip() if f_city.value else '',
                    driver_phone=f_driver.value.strip() if f_driver.value else '',
                    owner_phone=f_owner.value.strip() if f_owner.value else '',
                    loading_address=f_loading.value.strip(),
                    unloading_address=f_unload.value.strip(),
                    total_booking=float(f_total.value),
                    payment_1=float(f_p1.value or 0),
                    payment_2=float(f_p2.value or 0),
                    payment_3=float(f_p3.value or 0),
                )
                if trip:
                    database.update_trip(trip['id'], **kwargs)
                    ui.notify('Trip updated successfully', type='positive')
                else:
                    database.add_trip(**kwargs)
                    ui.notify('Trip saved successfully', type='positive')
                dialog.close()
                on_save()

            ui.button('Save Trip', on_click=_save).style(
                'background-color: #1e3a5f; color: #fff; border-radius: 6px;'
            ).props('icon=save')

    dialog.open()


def _section_label(text: str):
    ui.label(text).style(
        'color: #2d5a8e; font-size: 10px; font-weight: 700; '
        'text-transform: uppercase; letter-spacing: 0.8px; margin-top: 12px; margin-bottom: 4px;'
    )


def _field(label: str, trip, field: str, input_type: str, hint: str = ''):
    value = str(trip[field]) if trip and trip.get(field) is not None else ''
    inp = ui.input(label=label, value=value).style('min-width: 180px; flex: 1;')
    if input_type == 'date':
        inp.props('type=date')
    if hint:
        inp.props(f'hint="{hint}"')
    return inp


def _validate(date_val, vehicle_val, state_val, city_val,
              driver_val, owner_val, loading_val, unload_val,
              total_val, p1_val, p2_val, p3_val) -> list[str]:
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
