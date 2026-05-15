from nicegui import ui
import database
from ui.trips import trips_page
from ui.insights import insights_page

database.init_db()


GLOBAL_CSS = '''
    body { margin: 0; font-family: "Inter", "Segoe UI", sans-serif; }
    .nicegui-content { padding: 0 !important; }
    .q-drawer  { border-right: none !important; top: 0 !important; }
    .q-page-container { padding-top: 0 !important; background-color: #f4f7fb; }
    .q-page    { background-color: #f4f7fb; display: flex; flex-direction: column; }
    .q-layout  { min-height: 100vh; }
'''


@ui.page('/')
def index(new: str = ''):
    ui.add_css(GLOBAL_CSS)
    trips_page(open_new=(new == '1'))


@ui.page('/insights')
def insights():
    ui.add_css(GLOBAL_CSS)
    insights_page()


ui.run(
    title='TripLog',
    port=8080,
    reload=False,
    show=True,
    favicon='🚛',
)
