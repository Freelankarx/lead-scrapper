"""
Google Search Scraper — scrapes business leads from Google search results.
Uses rotating User-Agents and requests. No API key required.
"""

import re
import logging
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from app.utils.contact_extractor import extract_contacts

logger = logging.getLogger("freelankarx.google")


HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0"},
]


class GoogleScraper:
    name = "Google"

    async def scrape(self, niche: str, country: str = "", location: str = "", limit: int = 50, include_social: bool = True) -> list:
        leads = []
        query_parts = [niche]
        if location:
            query_parts.append(location)
        if country:
            query_parts.append(country)

        # Try multiple search patterns for better coverage
        queries = [
            f'{niche} business email site:linkedin.com OR site:facebook.com OR site:yelp.com {country}',
            f'"{niche}" contact email phone {location} {country}',
            f'{niche} company "email" OR "contact us" {location} {country}',
            f'list of {niche} businesses {country} {location}',
        ]

        session = requests.Session()
        for q_idx, query in enumerate(queries):
            if len(leads) >= limit:
                break
            try:
                urls = self._search_google(session, query, q_idx)
                # Visit each result and extract contacts
                for url in urls[:8]:
                    if len(leads) >= limit:
                        break
                    r = self._scrape_page(session, url, niche, country, location, include_social)
                    if isinstance(r, dict) and r.get("business_name"):
                        leads.append(r)
                time.sleep(1.5)  # polite delay
            except Exception as e:
                logger.debug(f"Google query {q_idx} failed: {e}")

        session.close()
        return leads[:limit]

    def _search_google(self, session, query: str, offset: int = 0) -> list:
        """Fetch Google search result URLs."""
        import random
        url = f"https://www.google.com/search?q={quote_plus(query)}&start={offset * 10}&num=10"
        headers = random.choice(HEADERS_LIST)
        headers["Accept-Language"] = "en-US,en;q=0.9"

        try:
            resp = session.get(url, headers=headers, allow_redirects=True, timeout=20)
            if resp.status_code != 200:
                return []
            soup = BeautifulSoup(resp.text, "html.parser")
            urls = []
            for a in soup.select("div.yuRUbf a, div.r a, h3.r a, .tF2Cxc a"):
                href = a.get("href", "")
                if href.startswith("http") and "google.com" not in href:
                    urls.append(href)
            return list(dict.fromkeys(urls))[:10]
        except Exception:
            return []

    def _scrape_page(self, session, url: str, niche: str, country: str, location: str, include_social: bool) -> dict:
        """Visit a URL and extract lead data."""
        import random
        headers = random.choice(HEADERS_LIST)
        try:
            resp = session.get(url, headers=headers, allow_redirects=True, timeout=12)
            if resp.status_code != 200:
                return {}
            soup = BeautifulSoup(resp.text, "html.parser")

            contacts = extract_contacts(resp.text, soup, url, include_social)

            # Get business name from title or OG tags
            title = ""
            og_title = soup.find("meta", property="og:title")
            if og_title:
                title = og_title.get("content", "")
            if not title:
                t = soup.find("title")
                title = t.get_text(strip=True) if t else ""
            # Clean title
            title = re.sub(r"\s*[-|–|·].*$", "", title).strip()
            title = title[:80] if title else ""

            if not title and not contacts.get("email") and not contacts.get("phone"):
                return {}

            lead = {
                "business_name": title,
                "owner_name": contacts.get("owner_name", ""),
                "email": contacts.get("email", ""),
                "phone": contacts.get("phone", ""),
                "website": url,
                "address": contacts.get("address", ""),
                "city": location or contacts.get("city", ""),
                "state": contacts.get("state", ""),
                "country": country or contacts.get("country", ""),
                "facebook": contacts.get("facebook", "") if include_social else "",
                "instagram": contacts.get("instagram", "") if include_social else "",
                "linkedin": contacts.get("linkedin", "") if include_social else "",
                "twitter": contacts.get("twitter", "") if include_social else "",
                "source": "Google",
            }
            return lead
        except Exception as e:
            logger.debug(f"Page scrape failed {url}: {e}")
            return {}
