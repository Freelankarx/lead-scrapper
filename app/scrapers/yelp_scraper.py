"""
Yelp Business Directory Scraper
Extracts business leads from Yelp search results
"""

import asyncio
import aiohttp
import re
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from app.utils.contact_extractor import extract_contacts

logger = logging.getLogger("freelankarx.yelp")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


class YelpScraper:
    name = "Yelp"
    BASE = "https://www.yelp.com"

    async def scrape(self, niche: str, country: str = "", location: str = "", limit: int = 50, include_social: bool = True) -> list:
        leads = []
        loc_query = location or country or "United States"

        connector = aiohttp.TCPConnector(limit=5, ssl=False)
        timeout = aiohttp.ClientTimeout(total=25)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=HEADERS) as session:
            pages = max(1, limit // 10)
            for page in range(pages):
                if len(leads) >= limit:
                    break
                offset = page * 10
                url = f"{self.BASE}/search?find_desc={quote_plus(niche)}&find_loc={quote_plus(loc_query)}&start={offset}"
                try:
                    biz_urls = await self._get_listing_urls(session, url)
                    tasks = [self._scrape_business(session, bu, niche, country, location, include_social) for bu in biz_urls[:5]]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for r in results:
                        if isinstance(r, dict) and r.get("business_name"):
                            leads.append(r)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.debug(f"Yelp page {page} failed: {e}")

        return leads[:limit]

    async def _get_listing_urls(self, session, url: str) -> list:
        try:
            async with session.get(url) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                urls = []
                for a in soup.select('a[href*="/biz/"]'):
                    href = a.get("href", "")
                    if "/biz/" in href and "?" not in href:
                        full = self.BASE + href if href.startswith("/") else href
                        if full not in urls:
                            urls.append(full)
                return urls[:10]
        except Exception:
            return []

    async def _scrape_business(self, session, url: str, niche: str, country: str, location: str, include_social: bool) -> dict:
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                contacts = extract_contacts(html, soup, url, include_social)

                # Business name
                h1 = soup.find("h1")
                name = h1.get_text(strip=True) if h1 else ""

                # Address from Yelp structured data
                addr_el = soup.select_one('[class*="address"]')
                address = addr_el.get_text(" ", strip=True) if addr_el else contacts.get("address", "")

                # Category
                cat_el = soup.select_one('[class*="category"] a')
                category = cat_el.get_text(strip=True) if cat_el else niche

                if not name:
                    return {}

                return {
                    "business_name": name,
                    "owner_name": contacts.get("owner_name", ""),
                    "email": contacts.get("email", ""),
                    "phone": contacts.get("phone", ""),
                    "website": contacts.get("website", url),
                    "address": address,
                    "city": location or contacts.get("city", ""),
                    "state": contacts.get("state", ""),
                    "country": country or "United States",
                    "category": category,
                    "facebook": contacts.get("facebook", "") if include_social else "",
                    "instagram": contacts.get("instagram", "") if include_social else "",
                    "linkedin": contacts.get("linkedin", "") if include_social else "",
                    "twitter": contacts.get("twitter", "") if include_social else "",
                    "source": "Yelp",
                }
        except Exception as e:
            logger.debug(f"Yelp biz scrape failed: {e}")
            return {}
