"""Static company info used across all invoice PDF templates."""
from pathlib import Path

_LOGO_ABS = Path(__file__).parent / "assets" / "jb_logo.png"

COMPANY = {
    "name": "JB Transports",
    "tagline": "Service All Over India and All Types of Vehicle",
    "address": "Survey No 711, Shiv Parking 1, Aslali Ring Road, Daskroi, Aslali, Ahmedabad 382427",
    "branch_office_address": "Survey No 711, Shiv Parking 1, Aslali Ring Road, Daskroi, Aslali, Ahmedabad 382427",
    "jurisdiction": "Ahmedabad",
    "phones": ["7600224710"],
    "email": "jb.transport363@gmail.com",
    "website": "",
    "transport_reg_no": "UDYAM-GJ-01-0650016",
    "pan": "AUWPB0355R",
    "gst": "24DKCPP6873H2ZS",
    # Defaults shown in the New Invoice form's Bank Details section. Users can
    # override any of these per invoice; the LR template uses inv.bank_* first,
    # falling back to these constants only when the per-invoice field is blank.
    "bank": {
        "account_no": "8866719574",
        "ifsc": "KKBK302609",
        "ac_holder": "JB TRANSPORTS",
        "bank_name": "KOTAK MAHINDRA BANK",
        "pan_holder": "ANKIT MAHADEVBHAI PAWAR",
        "pan_number": "DKCPP6873H",
    },
    "logo_path": str(_LOGO_ABS),
    "logo_url": _LOGO_ABS.as_uri(),  # file:///... — WeasyPrint reads this from an <img src>
}
