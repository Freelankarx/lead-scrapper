"""
Lead Deduplicator — removes duplicate leads using multiple matching strategies.
"""

import re
import logging

logger = logging.getLogger("freelankarx.dedup")


def normalize(s: str) -> str:
    """Lowercase, remove punctuation/spaces for comparison."""
    if not s:
        return ""
    return re.sub(r"[^a-z0-9]", "", s.lower())


def deduplicate(leads: list) -> list:
    """
    Remove duplicates by:
    1. Exact email match
    2. Exact phone match (normalized)
    3. Very similar business name + same city
    """
    seen_emails = set()
    seen_phones = set()
    seen_name_city = set()
    unique = []

    for lead in leads:
        email = lead.get("email", "").lower().strip()
        phone = re.sub(r"\D", "", lead.get("phone", ""))
        name = normalize(lead.get("business_name", ""))
        city = normalize(lead.get("city", ""))

        # Dedup by email
        if email and email in seen_emails:
            continue

        # Dedup by phone (only if 10+ digits)
        if phone and len(phone) >= 10 and phone in seen_phones:
            continue

        # Dedup by name+city combo
        name_city = f"{name}|{city}"
        if name and len(name) > 3 and name_city in seen_name_city:
            continue

        # Accept this lead
        if email:
            seen_emails.add(email)
        if phone and len(phone) >= 10:
            seen_phones.add(phone)
        if name and len(name) > 3:
            seen_name_city.add(name_city)

        unique.append(lead)

    removed = len(leads) - len(unique)
    logger.info(f"Deduplication: removed {removed} duplicates, kept {len(unique)}")
    return unique
