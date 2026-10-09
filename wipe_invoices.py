"""Wipe all invoices and reset the invoice sequence counter.

Usage:
    python wipe_invoices.py
    python wipe_invoices.py --db path/to/trips.db
    python wipe_invoices.py --yes          # skip confirmation
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def wipe(db_path: Path) -> None:
    if not db_path.exists():
        sys.exit(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            "DELETE FROM invoices;"
            "DELETE FROM invoice_sequences;"
            "DELETE FROM sqlite_sequence WHERE name='invoices';"
        )
        conn.commit()

        conn.isolation_level = None
        conn.execute("VACUUM")
    finally:
        conn.close()

    print("invoices wiped - next serial will be 1")


def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe invoices from the trips database.")
    parser.add_argument("--db", default="trips.db", help="Path to the SQLite database (default: trips.db)")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    args = parser.parse_args()

    db_path = Path(args.db)

    if not args.yes:
        answer = input(f"This will DELETE all invoices in {db_path}. Continue? [y/N] ").strip().lower()
        if answer not in {"y", "yes"}:
            print("Aborted.")
            return

    wipe(db_path)


if __name__ == "__main__":
    main()