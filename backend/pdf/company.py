"""Static company info used across all invoice PDF templates."""
from pathlib import Path

_LOGO_ABS = Path(__file__).parent / "assets" / "jb_logo.png"

COMPANY = {
    "name": "JB Transports",
    "address": "201, Shine Swasti, Nr. Godrej Garden City, Gota, Ahmedabad-382470",
    "jurisdiction": "Ahmedabad",
    "contact_person": "Dattaji Patil",
    "phones": ["7600224710", "9328448057"],
    "pan": "AUWPB0355R",
    "logo_path": str(_LOGO_ABS),
    "logo_url": _LOGO_ABS.as_uri(),  # file:///... — WeasyPrint reads this from an <img src>
}
