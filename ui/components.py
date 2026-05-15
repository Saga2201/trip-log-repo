from nicegui import ui


SIDEBAR_BG = '#1e3a5f'
SIDEBAR_ACTIVE_BG = '#2d5a8e'
SIDEBAR_TEXT = '#a0bcd8'
PAGE_BG = '#f4f7fb'


def sidebar(active: str):
    """
    Renders the left navigation drawer.
    active: one of 'trips' | 'insights'
    """
    with ui.left_drawer(fixed=True).style(
        f'background-color: {SIDEBAR_BG}; width: 220px; padding: 0; border: none;'
    ):
        with ui.element('div').style(
            'padding: 20px 16px 24px; display: flex; align-items: center; gap: 10px;'
        ):
            ui.icon('local_shipping').style('color: #4fc3f7; font-size: 26px;')
            ui.label('TripLog').style('color: #ffffff; font-weight: 700; font-size: 18px;')

        _nav_item('list', 'All Trips', '/', active == 'trips')
        _nav_item('add_circle_outline', 'New Trip', '/?new=1', False)
        _nav_item('bar_chart', 'Insights', '/insights', active == 'insights')

        ui.separator().style('background-color: #2d5a8e; margin: 12px 0;')

        with ui.element('div').style('padding: 8px 12px;'):
            with ui.element('div').style(
                'display: flex; align-items: center; gap: 8px; cursor: pointer; '
                'padding: 10px 12px; border: 1px solid #2d5a8e; border-radius: 6px;'
            ).on('click', _do_export):
                ui.icon('file_download').style(f'color: {SIDEBAR_TEXT}; font-size: 18px;')
                ui.label('Export to Excel').style(f'color: {SIDEBAR_TEXT}; font-size: 13px;')


def _nav_item(icon_name: str, label: str, path: str, is_active: bool):
    bg = f'background-color: {SIDEBAR_ACTIVE_BG}; border-left: 3px solid #4fc3f7;' if is_active else ''
    color = '#ffffff' if is_active else SIDEBAR_TEXT

    def go():
        ui.navigate.to(path)

    with ui.element('div').style(
        f'padding: 10px 16px; cursor: pointer; display: flex; align-items: center; gap: 10px; {bg}'
    ).on('click', go):
        ui.icon(icon_name).style(f'color: {color}; font-size: 18px;')
        ui.label(label).style(f'color: {color}; font-size: 13px;')


def _do_export():
    import database
    import export as exp
    trips = database.get_all_trips()
    if not trips:
        ui.notify('No trips to export.', type='warning')
        return
    path = exp.export_to_excel(trips)
    ui.notify(f'Exported to {path}', type='positive')
