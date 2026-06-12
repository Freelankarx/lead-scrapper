"""
Yellow Pages Business Directory Scraper
"""

import asyncio
import aiohttp
import logging
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from app.utils.contact_extractor import extract_contacts

logger = logging.getLogger("freelankarx.yellowpages")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


class YellowPagesScraper:
    name = "YellowPages"
    BASE = "https://www.yellowpages.com"

    async def scrape(self, niche: str, country: str = "", location: str = "", limit: int = 50, include_social: bool = True) -> list:
        leads = []
        loc = location or "New York, NY"

        connector = aiohttp.TCPConnector(limit=5, ssl=False)
        timeout = aiohttp.ClientTimeout(total=25)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=HEADERS) as session:
            pages = max(1, limit // 15)
            for page in range(1, pages + 1):
                if len(leads) >= limit:
                    break
                url = f"{self.BASE}/search?search_terms={quote_plus(niche)}&geo_location_terms={quote_plus(loc)}&page={page}"
                try:
                    page_leads = await self._scrape_listing_page(session, url, niche, country, location, include_social)
                    leads.extend(page_leads)
                    await asyncio.sleep(1.5)
                except Exception as e:
                    logger.debug(f"YP page {page} failed: {e}")

        return leads[:limit]

    async def _scrape_listing_page(self, session, url: str, niche: str, country: str, location: str, include_social: bool) -> list:
        leads = []
        try:
            async with session.get(url) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")

                listings = soup.select(".result")
                for listing in listings[:15]:
                    try:
                        name_el = listing.select_one(".business-name span")
                        name = name_el.get_text(strip=True) if name_el else ""
                        if not name:
                            continue

                        phone_el = listing.select_one(".phones.phone.primary")
                        phone = phone_el.get_text(strip=True) if phone_el else ""

                        addr_el = listing.select_one(".street-address")
                        city_el = listing.select_one(".city")
                        state_el = listing.select_one(".state")
                        address = addr_el.get_text(strip=True) if addr_el else ""
                        city = city_el.get_text(strip=True) if city_el else location
                        state = state_el.get_text(strip=True) if state_el else ""

                        website_el = listing.select_one('a[class*="track-visit-website"]')
                        website = website_el.get("href", "") if website_el else ""

                        # Try to visit website for email
                        email = ""
                        if website and website.startswith("http"):
                            try:
                                async with session.get(website, timeout=aiohttp.ClientTimeout(total=8)) as wr:
                                    whtml = await wr.text()
                                    wsoup = BeautifulSoup(whtml, "html.parser")
                                    wcontacts = extract_contacts(whtml, wsoup, website, include_social)
                                    email = wcontacts.get("email", "")
                            except Exception:
                                pass

                        leads.append({
                            "business_name": name,
                            "owner_name": "",
                            "email": email,
                            "phone": phone,
                            "website": website,
                            "address": address,
                            "city": city,
                            "state": state,
                            "country": country or "United States",
                            "source": "YellowPages",
                        })
                    except Exception:
                        continue
        except Exception as e:
            logger.debug(f"YP listing parse failed: {e}")

        return leads
