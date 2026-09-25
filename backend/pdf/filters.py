"""Custom Jinja filters used across invoice templates."""
from num2words import num2words


def inr_words(n) -> str:
    """Convert a rupee amount to Indian-style words (Lakh/Crore)."""
    if n is None:
        return ""
    rupees = int(round(float(n)))
    words = num2words(rupees, lang="en_IN")
    # num2words returns lowercase and hyphenated; title-case for bills.
    return f"Rupees {words.title()} Only"


def format_inr(n) -> str:
    """Format a number in Indian grouping: 100000 -> '1,00,000'."""
    if n is None or n == "":
        return ""
    try:
        num = float(n)
    except (TypeError, ValueError):
        return str(n)
    if num == 0:
        return "0"
    # Handle negatives and decimals separately.
    negative = num < 0
    num = abs(num)
    integer, dot, decimal = f"{num:.2f}".partition(".")
    # Trim trailing zeros in decimal but keep at least none.
    decimal = decimal.rstrip("0")
    # Indian grouping: last 3 digits, then groups of 2.
    if len(integer) <= 3:
        grouped = integer
    else:
        grouped = integer[-3:]
        rest = integer[:-3]
        while len(rest) > 2:
            grouped = rest[-2:] + "," + grouped
            rest = rest[:-2]
        grouped = rest + "," + grouped
    out = grouped + ("." + decimal if decimal else "")
    return ("-" if negative else "") + out
