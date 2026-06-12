"""
Lead Validator — validates emails, phones, and cleans data.
"""

import re
import logging

logger = logging.getLogger("freelankarx.validator")

# RFC-ish email validation
EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,7}$")

# Throwaway/spam domains to reject
SPAM_DOMAINS = {
    "example.com", "test.com", "foo.com", "bar.com", "mailinator.com",
    "guerrillamail.com", "trashmail.com", "yopmail.com", "10minutemail.com",
    "tempmail.com", "fakeinbox.com", "dispostable.com",
}

# Common TLDs for sanity check
VALID_TLDS = {
    "com", "net", "org", "io", "co", "biz", "info", "edu", "gov", "us", "uk",
    "ca", "au", "de", "fr", "ng", "za", "gh", "ke", "in", "sg", "ae", "ph",
    "nz", "mx", "br", "it", "es", "nl", "se", "no", "fi", "pl", "ru", "jp",
    "cn", "hk", "tw", "id", "my", "th", "vn", "pk", "bd", "eg", "ma", "tz"
}


def is_valid_email(email: str) -> bool:
    """Returns True if email looks legitimate."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip().lower()
    if not EMAIL_RE.match(email):
        return False
    domain = email.split("@")[-1].lower()
    if domain in SPAM_DOMAINS:
        return False
    tld = domain.split(".")[-1]
    if len(tld) < 2 or len(tld) > 7:
        return False
    # Reject emails with too many dots in local part (likely CSS/JS noise)
    local = email.split("@")[0]
    if local.count(".") > 4:
        return False
    return True


def clean_phone(phone: str) -> str:
    """Normalize phone number."""
    if not phone:
        return ""
    # Keep only digits, spaces, +, -, (), x
    cleaned = re.sub(r"[^\d\s\+\-\(\)xX]", "", phone).strip()
    digits_only = re.sub(r"\D", "", cleaned)
    if len(digits_only) < 7 or len(digits_only) > 15:
        return ""
    return cleaned


def clean_name(name: str) -> str:
    """Clean business name."""
    if not name:
        return ""
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\|.*$", "", name).strip()
    name = re.sub(r"[-–—].*$", "", name).strip()
    return name[:120]


def clean_url(url: str) -> str:
    """Normalize website URL."""
    if not url:
        return ""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    # Remove trailing slashes, tracking params
    url = re.sub(r"\?utm_.*", "", url)
    url = url.rstrip("/")
    return url[:300]


def validate_leads(leads: list) -> list:
    """Validate and clean a list of lead dicts."""
    validated = []
    for lead in leads:
        if not isinstance(lead, dict):
            continue

        email = lead.get("email", "")
        if email and not is_valid_email(email):
            lead["email"] = ""

        lead["phone"] = clean_phone(lead.get("phone", ""))
        lead["business_name"] = clean_name(lead.get("business_name", ""))
        lead["website"] = clean_url(lead.get("website", ""))

        # Skip entirely empty leads
        if not lead.get("business_name") and not lead.get("email") and not lead.get("phone"):
            continue

        validated.append(lead)

    logger.info(f"Validated {len(validated)}/{len(leads)} leads")
    return validated
