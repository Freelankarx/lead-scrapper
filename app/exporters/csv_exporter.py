"""
CSV Exporter
"""

import csv
import os
from datetime import datetime

FIELDS = [
    "business_name", "owner_name", "email", "phone", "website",
    "address", "city", "state", "country",
    "facebook", "instagram", "linkedin", "twitter", "source"
]

HEADERS = [
    "Business Name", "Owner Name", "Email", "Phone", "Website",
    "Address", "City", "State", "Country",
    "Facebook", "Instagram", "LinkedIn", "Twitter", "Source"
]


def export_csv(leads: list, output_dir: str, filename: str = None) -> str:
    if not filename:
        filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    path = os.path.join(output_dir, filename)

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writerow(dict(zip(FIELDS, HEADERS)))
        for lead in leads:
            writer.writerow({k: lead.get(k, "") for k in FIELDS})

    return path
