"""
Contact Extractor — extracts emails, phones, addresses, and social links from HTML.
"""

import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# Regex patterns
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,7}")
PHONE_RE = re.compile(
    r"(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
    r"|(\+\d{1,3}[\s-]?\d{1,4}[\s-]?\d{3,4}[\s-]?\d{3,4})"
)
# Obfuscated email patterns: name [at] domain [dot] com
OBFUSCATED_EMAIL_RE = re.compile(
    r"([a-zA-Z0-9._%+\-]+)\s*[\[\(]?at[\]\)]?\s*([a-zA-Z0-9.\-]+)\s*[\[\(]?dot[\]\)]?\s*([a-zA-Z]{2,7})",
    re.IGNORECASE
)

SOCIAL_PATTERNS = {
    "facebook":  re.compile(r"facebook\.com/(?!sharer|share|dialog|pages/create|events|groups/)([\w\.\-]+/?)", re.I),
    "instagram": re.compile(r"instagram\.com/([\w\.\-]+/?)", re.I),
    "linkedin":  re.compile(r"linkedin\.com/(?:company|in|pub)/([\w\.\-]+/?)", re.I),
    "twitter":   re.compile(r"(?:twitter|x)\.com/([\w\.\-]+/?)", re.I),
}


def extract_contacts(html: str, soup: BeautifulSoup, base_url: str, include_social: bool = True) -> dict:
    """Extract all contact info from a page."""
    result = {
        "email": "",
        "phone": "",
        "address": "",
        "city": "",
        "state": "",
        "country": "",
        "owner_name": "",
        "website": base_url,
    }

    # ─ Emails ─
    emails = EMAIL_RE.findall(html)
    # Filter out noise
    clean_emails = [
        e for e in emails
        if not any(x in e.lower() for x in [
            "example", "sentry", "wix", ".png", ".jpg", ".css", ".js",
            "noreply", "no-reply", "support@sentry", "test@"
        ])
    ]
    # Prefer contact/info/hello emails
    priority = [e for e in clean_emails if any(x in e.lower() for x in ["info@", "contact@", "hello@", "admin@", "sales@"])]
    result["email"] = priority[0] if priority else (clean_emails[0] if clean_emails else "")

    # Try obfuscated emails if none found
    if not result["email"]:
        text = soup.get_text(" ")
        obf = OBFUSCATED_EMAIL_RE.search(text)
        if obf:
            result["email"] = f"{obf.group(1)}@{obf.group(2)}.{obf.group(3)}"

    # ─ Phones ─
    phone_matches = PHONE_RE.findall(html)
    for match in phone_matches:
        ph = "".join(match).strip()
        ph = re.sub(r"\s+", " ", ph).strip()
        if len(re.sub(r"\D", "", ph)) >= 10:
            result["phone"] = ph
            break

    # Also check <a href="tel:...">
    if not result["phone"]:
        tel_link = soup.find("a", href=re.compile(r"^tel:"))
        if tel_link:
            result["phone"] = tel_link["href"].replace("tel:", "").strip()

    # ─ Address ─
    # Try schema.org structured data
    addr_schema = soup.find(attrs={"itemprop": "streetAddress"})
    if addr_schema:
        result["address"] = addr_schema.get_text(strip=True)
    city_schema = soup.find(attrs={"itemprop": "addressLocality"})
    if city_schema:
        result["city"] = city_schema.get_text(strip=True)
    state_schema = soup.find(attrs={"itemprop": "addressRegion"})
    if state_schema:
        result["state"] = state_schema.get_text(strip=True)
    country_schema = soup.find(attrs={"itemprop": "addressCountry"})
    if country_schema:
        result["country"] = country_schema.get_text(strip=True)

    # ─ Owner name ─
    owner_patterns = [
        re.compile(r"(?:owner|founder|ceo|director|president|manager)[:\s]+([A-Z][a-z]+\s[A-Z][a-z]+)", re.I),
        re.compile(r"([A-Z][a-z]+\s[A-Z][a-z]+)\s*[,—-]\s*(?:Owner|Founder|CEO|Director)", re.I),
    ]
    text = soup.get_text(" ")
    for pat in owner_patterns:
        m = pat.search(text)
        if m:
            result["owner_name"] = m.group(1).strip()
            break

    # ─ Social links ─
    if include_social:
        for link in soup.find_all("a", href=True):
            href = link["href"]
            for platform, pat in SOCIAL_PATTERNS.items():
                if not result.get(platform) and pat.search(href):
                    full = href if href.startswith("http") else urljoin(base_url, href)
                    result[platform] = full

        # Fallback: search raw HTML
        for platform, pat in SOCIAL_PATTERNS.items():
            if not result.get(platform):
                m = pat.search(html)
                if m:
                    result[platform] = f"https://{platform}.com/{m.group(1)}"

    return result
