from nicegui import ui
import database
from ui.trips import trips_page
from ui.insights import insights_page

database.init_db()


@ui.page('/')
def index(new: str = ''):
    ui.add_css('''
        body { margin: 0; font-family: "Inter", "Segoe UI", sans-serif; }
        .nicegui-content { padding: 0 !important; }
        .q-drawer { border-right: none !important; }
    ''')
    trips_page(open_new=(new == '1'))


@ui.page('/insights')
def insights():
    ui.add_css('''
        body { margin: 0; font-family: "Inter", "Segoe UI", sans-serif; }
        .nicegui-content { padding: 0 !important; }
        .q-drawer { border-right: none !important; }
    ''')
    insights_page()


ui.run(
    title='TripLog',
    port=8080,
    reload=False,
    show=True,
    favicon='🚛',
)
