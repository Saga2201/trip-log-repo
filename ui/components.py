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
        f'background-color: {SIDEBAR_BG}; width: 200px; padding: 0; border: none;'
    ):
        ui.label('🚛 TripLog').style(
            'color: #ffffff; font-weight: 700; font-size: 16px; '
            'padding: 20px 16px 24px; display: block;'
        )

        _nav_item('📋 All Trips', '/', active == 'trips')
        _nav_item('➕ New Trip', '/?new=1', active == 'trips')
        _nav_item('📊 Insights', '/insights', active == 'insights')

        ui.separator().style('background-color: #2d5a8e; margin: 8px 0;')

        with ui.element('div').style('padding: 8px 12px;'):
            ui.button('📤 Export to Excel', on_click=_do_export).style(
                'background-color: transparent; color: #a0bcd8; border: 1px solid #2d5a8e; '
                'width: 100%; font-size: 12px; padding: 8px;'
            ).props('flat')


def _nav_item(label: str, path: str, is_active: bool):
    bg = f'background-color: {SIDEBAR_ACTIVE_BG}; border-left: 3px solid #4fc3f7;' if is_active else ''
    color = '#ffffff' if is_active else SIDEBAR_TEXT

    def go():
        ui.navigate.to(path)

    with ui.element('div').style(
        f'padding: 10px 16px; cursor: pointer; {bg}'
    ).on('click', go):
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
