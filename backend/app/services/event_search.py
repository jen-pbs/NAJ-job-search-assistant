import asyncio
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright

from app.models.events import Event

_executor = ThreadPoolExecutor(max_workers=1)

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime: {}};
"""

EVENT_SITES = [
    # Event platforms
    "eventbrite.com",
    "meetup.com",
    "lu.ma",
    # HEOR / Health economics associations
    "ispor.org",
    "smdm.org",
    "academyhealth.org",
    "ashecon.org",
    "healtheconomics.org",
    # Pharma / Biotech
    "biocom.org",
    "bio.org",
    "biopharmadive.com",
    "informaconnect.com",
    "becarispublishing.com",
    # Career fairs
    "biospace.com",
    "careers.pharmiweb.com",
    "scilife.io",
]


def _is_specific_event_url(url: str) -> bool:
    """Return True only if the URL points to a specific event, not a listing/directory page."""
    if not url or not url.startswith("http"):
        return False

    # Block known non-event patterns
    if "linkedin.com" in url:
        return False

    # Eventbrite: only /e/ URLs are specific events
    if "eventbrite.com" in url:
        return "/e/" in url

    # Meetup: only /events/ paths with a specific event ID are real events
    if "meetup.com" in url:
        return "/events/" in url

    # Lu.ma: specific event pages have a short slug after the domain
    if "lu.ma" in url:
        parts = url.rstrip("/").split("/")
        return len(parts) > 3 and len(parts[-1]) > 2

    # For all other sites: reject homepages and generic directories
    # A specific event URL typically has 3+ path segments
    path = re.sub(r"^https?://[^/]+", "", url).rstrip("/")
    if not path or path == "/":
        return False

    # Reject common directory patterns
    reject = [
        "/find/", "/search", "/discover", "/category/", "/topics/",
        "/blog/", "/about", "/contact", "/pricing",
        "/d/", "/b/", "/cc/", "/o/",
    ]
    if any(r in path.lower() for r in reject):
        return False

    # Must have at least one meaningful path segment beyond the domain
    segments = [s for s in path.split("/") if s]
    return len(segments) >= 1


def _search_events_sync(query: str, location: str | None, max_results: int = 15) -> list[dict]:
    """Search DuckDuckGo for events matching the query."""
    results = []

    loc_str = f" {location}" if location else ""

    # Group sites for different query focuses
    platform_sites = " OR ".join(f"site:{s}" for s in ["eventbrite.com", "meetup.com", "lu.ma"])
    heor_sites = " OR ".join(f"site:{s}" for s in ["ispor.org", "ashecon.org", "academyhealth.org", "smdm.org", "healtheconomics.org"])
    pharma_sites = " OR ".join(f"site:{s}" for s in ["biocom.org", "bio.org", "informaconnect.com", "biopharmadive.com"])

    queries = [
        f"({platform_sites}) {query} event conference 2026{loc_str}",
        f"({heor_sites}) {query} conference 2026",
        f"({pharma_sites}) {query} conference 2026",
        f"{query} networking event meetup 2026{loc_str}",
        f"{query} career fair pharma biotech health 2026{loc_str}",
    ]

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True, channel="chrome",
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
        except Exception:
            browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1366, "height": 768},
        )
        context.set_default_timeout(12000)
        context.add_init_script(STEALTH_JS)

        seen_urls: set[str] = set()

        for q in queries:
            if len(results) >= max_results:
                break

            try:
                page = context.new_page()
                page.goto(
                    f"https://duckduckgo.com/?q={q.replace(' ', '+')}",
                    wait_until="domcontentloaded",
                )
                time.sleep(random.uniform(2.0, 3.0))

                # Scroll for more results
                page.keyboard.press("End")
                time.sleep(1)

                articles = page.locator("article")
                count = articles.count()

                for i in range(count):
                    if len(results) >= max_results:
                        break
                    try:
                        article = articles.nth(i)
                        text = article.inner_text().strip()

                        # Find the real destination link (not DDG redirect)
                        href = ""
                        all_links = article.locator("a[href]")
                        for li in range(all_links.count()):
                            h = all_links.nth(li).get_attribute("href") or ""
                            if h and "duckduckgo.com" not in h and h.startswith("http"):
                                href = h
                                break

                        # Fallback: check data-href or extract from DDG redirect
                        if not href:
                            first_link = article.locator("a[href]").first
                            if first_link.count() > 0:
                                href = first_link.get_attribute("data-href") or first_link.get_attribute("href") or ""

                        if not href or "duckduckgo.com" in href or href in seen_urls:
                            continue

                        # Only allow URLs that look like specific events
                        if not _is_specific_event_url(href):
                            continue

                        clean_url = re.sub(r"\?.*$", "", href)
                        if clean_url in seen_urls:
                            continue
                        seen_urls.add(clean_url)

                        parsed = _parse_event_result(text, clean_url)
                        if parsed:
                            results.append(parsed)
                    except Exception:
                        continue

                page.close()
            except Exception as e:
                print(f"Event search error: {e}")

            if len(queries) > 1:
                time.sleep(random.uniform(1.0, 2.0))

        browser.close()

    return results


def _parse_event_result(text: str, url: str) -> dict | None:
    """Parse a DuckDuckGo article into event data."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if len(lines) < 2:
        return None

    # Determine source with friendly names
    source_names = {
        "eventbrite": "Eventbrite", "meetup": "Meetup", "lu": "Luma",
        "ispor": "ISPOR", "smdm": "SMDM", "academyhealth": "AcademyHealth",
        "ashecon": "ASHEcon", "healtheconomics": "IHEA",
        "biocom": "Biocom", "bio": "BIO", "biopharmadive": "BioPharma Dive",
        "informaconnect": "Informa", "becarispublishing": "Becaris",
        "biospace": "BioSpace", "pharmiweb": "PharmiWeb", "scilife": "Scilife",
    }
    source = None
    url_lower = url.lower()
    for key, name in source_names.items():
        if key in url_lower:
            source = name
            break
    if not source:
        domain = re.search(r"https?://(?:www\.)?([^/]+)", url)
        source = domain.group(1) if domain else "Web"

    # Extract title and description
    title = ""
    description = ""
    date = None
    location = None

    for line in lines:
        if "http" in line.lower() or len(line) < 10:
            continue
        # Skip generic lines
        if line.lower().startswith(("share this", "save this", "join ", "through ")):
            if not description and len(line) > 40:
                description = line
            continue
        if not title and len(line) > 15 and len(line) < 120:
            title = line
        elif not description and len(line) > 30:
            description = line

    if not title:
        return None

    # Clean title
    title = re.sub(r"\s*\|.*$", "", title).strip()
    title = re.sub(r"\s*-\s*(Eventbrite|Meetup|Lu\.ma).*$", "", title, flags=re.IGNORECASE).strip()

    # Try to find date patterns
    full_text = " ".join(lines)
    date_match = re.search(
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2}(?:\s*[-–]\s*\d{1,2})?,?\s*\d{4})",
        full_text,
        re.IGNORECASE,
    )
    if date_match:
        date = date_match.group(1).strip()

    if not date:
        date_match2 = re.search(r"(\d{1,2}/\d{1,2}/\d{2,4})", full_text)
        if date_match2:
            date = date_match2.group(1)

    # Try to find location
    loc_match = re.search(
        r"(?:in|at|Location:)\s+([A-Z][^.·\n]{3,40})",
        full_text,
        re.IGNORECASE,
    )
    if loc_match:
        location = loc_match.group(1).strip()

    # Additional date patterns: "May 17 - 20, 2026" or "May 17-20"
    if not date:
        date_match3 = re.search(
            r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:\s*[-–]\s*(?:\w+\s+)?\d{1,2})?,?\s*\d{4})",
            full_text,
            re.IGNORECASE,
        )
        if date_match3:
            date = date_match3.group(1).strip()

    # Check for virtual
    if re.search(r"\b(virtual|online|webinar|zoom)\b", full_text, re.IGNORECASE):
        location = location or "Virtual"

    # Detect free events
    is_free = None
    if re.search(r"\b(free|no cost|complimentary|free admission|free entry|\$0)\b", full_text, re.IGNORECASE):
        is_free = True
    elif re.search(r"\b(\$\d+|paid|registration fee|ticket price|early.?bird)\b", full_text, re.IGNORECASE):
        is_free = False

    return {
        "title": title[:150],
        "url": url,
        "date": date,
        "location": location,
        "source": source,
        "description": description[:300] if description else None,
        "is_free": is_free,
    }


async def search_events(
    query: str,
    location: str | None = None,
    max_results: int = 15,
) -> tuple[list[Event], str]:
    """Search for events related to the query."""
    loop = asyncio.get_event_loop()
    raw_results = await loop.run_in_executor(
        _executor, _search_events_sync, query, location, max_results
    )

    events = [Event(**r) for r in raw_results if r.get("url") and r["url"].startswith("http")]
    search_desc = f"{query} events" + (f" in {location}" if location else "")
    return events, search_desc
