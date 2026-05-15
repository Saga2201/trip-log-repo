from collections import defaultdict
from datetime import date
import plotly.graph_objects as go
from nicegui import ui
import database
from helpers import calc_pending, calc_received, calc_status
from ui.components import sidebar, PAGE_BG


def insights_page():
    sidebar('insights')

    trips = database.get_all_trips()

    # Enrich each trip with derived fields
    enriched = []
    for t in trips:
        p1, p2, p3 = t['payment_1'], t['payment_2'], t['payment_3']
        pending = calc_pending(t['total_booking'], p1, p2, p3)
        enriched.append({
            **t,
            'received': calc_received(p1, p2, p3),
            'pending':  pending,
            'status':   calc_status(pending, p1, p2, p3),
        })

    total_revenue  = sum(t['total_booking'] for t in enriched)
    total_pending  = sum(t['pending'] for t in enriched)
    total_trips    = len(enriched)
    avg_booking    = (total_revenue / total_trips) if total_trips else 0

    with ui.element('div').style(f'background-color: {PAGE_BG}; min-height: 100vh; padding: 24px; box-sizing: border-box;'):
        ui.label('📊 Business Insights').style('font-size: 20px; font-weight: 700; color: #1e3a5f; margin-bottom: 20px;')

        # ── KPI Cards ─────────────────────────────────────────────────
        with ui.row().style('gap: 16px; margin-bottom: 24px; flex-wrap: wrap;'):
            _kpi('Total Revenue',    f'₹{total_revenue:,.0f}',  '#1e3a5f')
            _kpi('Total Pending',    f'₹{total_pending:,.0f}',  '#e53935')
            _kpi('Total Trips',      str(total_trips),           '#f57c00')
            _kpi('Avg. Booking',     f'₹{avg_booking:,.0f}',    '#7b1fa2')

        # ── Row 2: Monthly chart + Pending list ────────────────────────
        with ui.row().style('gap: 16px; margin-bottom: 16px; flex-wrap: wrap; align-items: flex-start;'):

            # Monthly Revenue Bar Chart
            with ui.card().style('flex: 1.6; min-width: 300px; padding: 16px; border-radius: 8px;'):
                ui.label('Monthly Revenue (₹)').style('font-size: 13px; font-weight: 700; color: #1e3a5f; margin-bottom: 8px;')
                monthly = _monthly_revenue(enriched)
                fig = go.Figure(data=[go.Bar(
                    x=list(monthly.keys()),
                    y=list(monthly.values()),
                    marker_color='#1e3a5f',
                )])
                fig.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=220,
                    paper_bgcolor='white',
                    plot_bgcolor='white',
                    yaxis=dict(gridcolor='#f0f4f8'),
                )
                ui.plotly(fig).style('width: 100%;')

            # Pending Payments List
            with ui.card().style('flex: 1; min-width: 220px; padding: 16px; border-radius: 8px;'):
                ui.label('⚠️ Pending Payments').style('font-size: 13px; font-weight: 700; color: #e53935; margin-bottom: 8px;')
                pending_trips = sorted(
                    [t for t in enriched if t['pending'] > 0],
                    key=lambda t: t['pending'], reverse=True
                )
                if not pending_trips:
                    ui.label('All trips are fully paid ✅').style('color: #888; font-size: 12px;')
                for t in pending_trips[:10]:
                    with ui.element('div').style('border-bottom: 1px solid #f5f5f5; padding: 6px 0;'):
                        with ui.row().style('justify-content: space-between; align-items: center;'):
                            with ui.column().style('gap: 0;'):
                                ui.label(t['vehicle_number']).style('font-size: 12px; font-weight: 600; color: #333;')
                                ui.label(f"{t['loading_address']} → {t['unloading_address']} · {t['date']}").style('font-size: 10px; color: #888;')
                            ui.label(f"₹{t['pending']:,.0f}").style('font-size: 12px; font-weight: 700; color: #e53935;')

        # ── Row 3: Vehicle-wise + State-wise ──────────────────────────
        with ui.row().style('gap: 16px; flex-wrap: wrap; align-items: flex-start;'):

            # Vehicle-wise table
            with ui.card().style('flex: 1; min-width: 260px; padding: 16px; border-radius: 8px;'):
                ui.label('🚛 Vehicle-wise Summary').style('font-size: 13px; font-weight: 700; color: #1e3a5f; margin-bottom: 8px;')
                vehicle_data = _vehicle_summary(enriched)
                cols = [
                    {'name': 'vehicle', 'label': 'Vehicle',   'field': 'vehicle'},
                    {'name': 'trips',   'label': 'Trips',     'field': 'trips'},
                    {'name': 'earnings','label': 'Earnings ₹','field': 'earnings'},
                ]
                rows = [{'vehicle': v, 'trips': d['trips'], 'earnings': f"₹{d['earnings']:,.0f}"} for v, d in vehicle_data.items()]
                ui.table(columns=cols, rows=rows, row_key='vehicle').style('font-size: 12px;')

            # State-wise breakdown
            with ui.card().style('flex: 1; min-width: 260px; padding: 16px; border-radius: 8px;'):
                ui.label('📍 State-wise Trip Count').style('font-size: 13px; font-weight: 700; color: #1e3a5f; margin-bottom: 12px;')
                state_data = _state_summary(enriched)
                max_trips = max((v for v in state_data.values()), default=1)
                for state, count in sorted(state_data.items(), key=lambda x: -x[1])[:8]:
                    pct = int((count / max_trips) * 100)
                    with ui.element('div').style('margin-bottom: 8px;'):
                        with ui.row().style('justify-content: space-between; margin-bottom: 2px;'):
                            ui.label(state or '—').style('font-size: 11px; font-weight: 600; color: #333;')
                            ui.label(f'{count} trips').style('font-size: 11px; color: #888;')
                        with ui.element('div').style('background: #f0f4f8; border-radius: 4px; height: 8px; overflow: hidden;'):
                            ui.element('div').style(f'background: #1e3a5f; width: {pct}%; height: 100%; border-radius: 4px;')


def _kpi(title: str, value: str, accent: str):
    with ui.card().style(
        f'flex: 1; min-width: 150px; border-left: 4px solid {accent}; '
        'padding: 12px 16px; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.07);'
    ):
        ui.label(title).style('color: #888; font-size: 10px; text-transform: uppercase; letter-spacing: 0.5px;')
        ui.label(value).style(f'color: {accent}; font-size: 22px; font-weight: 700; margin-top: 4px;')


def _monthly_revenue(trips: list) -> dict:
    current_year = str(date.today().year)
    months = {f'{current_year}-{m:02d}': 0.0 for m in range(1, 13)}
    for t in trips:
        month_key = t['date'][:7]
        if month_key in months:
            months[month_key] += t['total_booking']
    labels = {
        f'{current_year}-01': 'Jan', f'{current_year}-02': 'Feb',
        f'{current_year}-03': 'Mar', f'{current_year}-04': 'Apr',
        f'{current_year}-05': 'May', f'{current_year}-06': 'Jun',
        f'{current_year}-07': 'Jul', f'{current_year}-08': 'Aug',
        f'{current_year}-09': 'Sep', f'{current_year}-10': 'Oct',
        f'{current_year}-11': 'Nov', f'{current_year}-12': 'Dec',
    }
    return {labels[k]: v for k, v in months.items()}


def _vehicle_summary(trips: list) -> dict:
    summary = defaultdict(lambda: {'trips': 0, 'earnings': 0.0})
    for t in trips:
        v = t['vehicle_number']
        summary[v]['trips'] += 1
        summary[v]['earnings'] += t['total_booking']
    return dict(sorted(summary.items(), key=lambda x: -x[1]['earnings']))


def _state_summary(trips: list) -> dict:
    summary = defaultdict(int)
    for t in trips:
        summary[t.get('state', '') or 'Unknown'] += 1
    return dict(summary)
