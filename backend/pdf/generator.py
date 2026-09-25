"""Render invoice PDFs from HTML templates via WeasyPrint."""
import io
import zipfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS

from backend.pdf.company import COMPANY
from backend.pdf.filters import inr_words, format_inr

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)
_env.filters["inr_words"] = inr_words
_env.filters["format_inr"] = format_inr

_KIND_TO_TEMPLATE = {
    "lr": "lr.html",
    "party_bill": "party_bill.html",
    "driver_bill": "driver_bill.html",
}


def render_pdf(kind: str, invoice: dict) -> bytes:
    template_name = _KIND_TO_TEMPLATE.get(kind)
    if not template_name:
        raise ValueError(f"unknown kind: {kind!r}")
    template = _env.get_template(template_name)
    html = template.render(inv=invoice, company=COMPANY)
    base_css = CSS(filename=str(_TEMPLATES_DIR / "_base.css"))
    return HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf(stylesheets=[base_css])


def render_all_zip(invoice: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for kind in ("lr", "party_bill", "driver_bill"):
            z.writestr(f"{invoice['serial_number'].replace('/', '_')}_{kind}.pdf",
                       render_pdf(kind, invoice))
    return buf.getvalue()
