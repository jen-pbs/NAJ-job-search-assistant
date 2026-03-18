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
    "eventbrite.com",
    "meetup.com",
    "lu.ma",
    "ispor.org",
    "smdm.org",
    "academyhealth.org",
]


def _search_events_sync(query: str, location: str | None, max_results: int = 15) -> list[dict]:
    """Search DuckDuckGo for events matching the query."""
    results = []

    site_filter = " OR ".join(f"site:{s}" for s in EVENT_SITES[:3])
    search_query = f"{query} event conference 2026"
    if location:
        search_query += f" {location}"

    queries = [
        f"({site_filter}) {search_query}",
        f"{query} conference 2026 HEOR health economics",
        f"{query} networking event meetup 2026",
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

                        # Find first link in article
                        link_el = article.locator("a[href]").first
                        if link_el.count() == 0:
                            continue
                        href = link_el.get_attribute("href") or ""

                        if not href or href in seen_urls:
                            continue

                        # Skip non-event results
                        if "linkedin.com" in href:
                            continue

                        clean_url = re.sub(r"\?.*$", "", href)
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

    # Determine source
    source = None
    for site in EVENT_SITES:
        if site.split(".")[0] in url.lower():
            source = site.split(".")[0].capitalize()
            break
    if not source:
        domain = re.search(r"https?://(?:www\.)?([^/]+)", url)
        source = domain.group(1) if domain else "Web"

    # Extract title (usually the longest meaningful line that's not a URL)
    title = ""
    description = ""
    date = None
    location = None

    for line in lines:
        if "http" in line.lower() or len(line) < 10:
            continue
        if not title and len(line) > 15:
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

    # Check for virtual
    if re.search(r"\b(virtual|online|webinar|zoom)\b", full_text, re.IGNORECASE):
        location = location or "Virtual"

    return {
        "title": title[:150],
        "url": url,
        "date": date,
        "location": location,
        "source": source,
        "description": description[:300] if description else None,
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

    events = [Event(**r) for r in raw_results]
    search_desc = f"{query} events" + (f" in {location}" if location else "")
    return events, search_desc
