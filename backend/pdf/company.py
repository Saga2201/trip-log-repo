"""Static company info used across all invoice PDF templates."""
from pathlib import Path

_LOGO_ABS = Path(__file__).parent / "assets" / "jb_logo.png"

COMPANY = {
    "name": "JB Transports",
    "tagline": "Transport Services Full Load and Part Load Service All Over India",
    "address": "201, Shine Swasti, Nr. Godrej Garden City, Gota, Ahmedabad-382470",
    "branch_office_address": "201, Shine Swasti, Nr. Godrej Garden City, Gota, Ahmedabad-382470",
    "jurisdiction": "Ahmedabad",
    "phones": ["7600224710"],
    "email": "",
    "website": "",
    "transport_reg_no": "",
    "pan": "AUWPB0355R",
    "gst": "24DKCPP6873H2ZS",
    "bank": {
        "account_no": "",
        "ifsc": "",
        "ac_holder": "JB Transports",
        "bank_name": "",
        "pan_holder": "",
        "pan_number": "AUWPB0355R",
    },
    "logo_path": str(_LOGO_ABS),
    "logo_url": _LOGO_ABS.as_uri(),  # file:///... — WeasyPrint reads this from an <img src>
}
