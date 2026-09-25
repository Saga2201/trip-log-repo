"""Render invoice PDFs from HTML templates via WeasyPrint."""
import ctypes
import io
import os
import sys
import zipfile
from pathlib import Path


def _preload_weasyprint_libs_macos() -> None:
    """Pre-load Homebrew's GLib/Pango/Cairo shared libs on macOS.

    WeasyPrint's cffi loader calls ``dlopen('libgobject-2.0-0', ...)`` and
    friends, which fails on macOS because those short names are not on the
    default dyld search path. ``DYLD_FALLBACK_LIBRARY_PATH`` sometimes works
    but macOS SIP strips ``DYLD_*`` env vars from child processes of
    hardened Python builds (e.g. Command Line Tools framework), which
    breaks uvicorn's reload workers.

    Loading each dependency by absolute path with ``RTLD_GLOBAL`` up front
    makes the symbols reachable to any later ``dlopen`` in this process,
    regardless of env-var propagation.
    """
    if sys.platform != "darwin":
        return
    brew_prefix = None
    for candidate in ("/opt/homebrew", "/usr/local"):
        if os.path.isdir(os.path.join(candidate, "opt", "glib")):
            brew_prefix = candidate
            break
    if brew_prefix is None:
        return  # Homebrew not present — let WeasyPrint's own error explain.

    libdir = os.path.join(brew_prefix, "lib")
    # Also add to env so cffi's short-name lookup has a shot too.
    current = os.environ.get("DYLD_FALLBACK_LIBRARY_PATH", "")
    if libdir not in current:
        os.environ["DYLD_FALLBACK_LIBRARY_PATH"] = (
            libdir + (":" + current if current else "")
        )

    # Order matters: dependencies first, then things that depend on them.
    for libname in (
        "libintl.8.dylib",
        "libffi.8.dylib",
        "libgio-2.0.0.dylib",
        "libglib-2.0.0.dylib",
        "libgobject-2.0.0.dylib",
        "libgmodule-2.0.0.dylib",
        "libfontconfig.1.dylib",
        "libfreetype.6.dylib",
        "libharfbuzz.0.dylib",
        "libpixman-1.0.dylib",
        "libcairo.2.dylib",
        "libpango-1.0.0.dylib",
        "libpangoft2-1.0.0.dylib",
        "libpangocairo-1.0.0.dylib",
    ):
        for search in (libdir, f"{brew_prefix}/opt/glib/lib",
                       f"{brew_prefix}/opt/pango/lib", f"{brew_prefix}/opt/cairo/lib",
                       f"{brew_prefix}/opt/harfbuzz/lib",
                       f"{brew_prefix}/opt/fontconfig/lib",
                       f"{brew_prefix}/opt/pixman/lib",
                       f"{brew_prefix}/opt/gettext/lib",
                       f"{brew_prefix}/opt/libffi/lib"):
            full = os.path.join(search, libname)
            if os.path.exists(full):
                try:
                    ctypes.CDLL(full, mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass
                break


_preload_weasyprint_libs_macos()

from jinja2 import Environment, FileSystemLoader, select_autoescape  # noqa: E402
from weasyprint import HTML, CSS  # noqa: E402

from backend.pdf.company import COMPANY  # noqa: E402
from backend.pdf.filters import inr_words, format_inr  # noqa: E402

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


def render_pdf(kind: str, invoice: dict, copy_type: str = "consignor") -> bytes:
    template_name = _KIND_TO_TEMPLATE.get(kind)
    if not template_name:
        raise ValueError(f"unknown kind: {kind!r}")
    template = _env.get_template(template_name)
    html = template.render(inv=invoice, company=COMPANY, copy_type=copy_type)
    base_css = CSS(filename=str(_TEMPLATES_DIR / "_base.css"))
    return HTML(string=html, base_url=str(_TEMPLATES_DIR)).write_pdf(stylesheets=[base_css])


def render_all_zip(invoice: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for kind in ("lr", "party_bill", "driver_bill"):
            z.writestr(f"{invoice['serial_number'].replace('/', '_')}_{kind}.pdf",
                       render_pdf(kind, invoice))
    return buf.getvalue()
