import asyncio
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from collections import deque

from playwright.sync_api import sync_playwright

from app.models.schemas import LinkedInProfile

_executor = ThreadPoolExecutor(max_workers=2)

_search_timestamps: deque[float] = deque()
MAX_SEARCHES_PER_HOUR = 10

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = {runtime: {}};
"""


def _check_rate_limit() -> str | None:
    """Returns error message if rate limited, None if OK."""
    now = time.time()
    while _search_timestamps and _search_timestamps[0] < now - 3600:
        _search_timestamps.popleft()

    if len(_search_timestamps) >= MAX_SEARCHES_PER_HOUR:
        oldest = _search_timestamps[0]
        wait_minutes = int((oldest + 3600 - now) / 60) + 1
        return f"Rate limit reached ({MAX_SEARCHES_PER_HOUR} searches/hour). Try again in ~{wait_minutes} minutes."

    _search_timestamps.append(now)
    return None


def build_search_queries(
    query: str,
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
) -> list[str]:
    """Build search queries optimized for LinkedIn profile discovery."""
    base = "site:linkedin.com/in"
    parts = [base, query]

    if location:
        parts.append(f'"{location}"')

    if seniority:
        parts.append(f'"{seniority}"')

    if companies:
        company_clause = " OR ".join(f'"{c}"' for c in companies)
        parts.append(f"({company_clause})")

    queries = [" ".join(parts)]

    if companies and len(companies) > 5:
        mid = len(companies) // 2
        for chunk in [companies[:mid], companies[mid:]]:
            chunk_parts = [base, query]
            if location:
                chunk_parts.append(f'"{location}"')
            chunk_clause = " OR ".join(f'"{c}"' for c in chunk)
            chunk_parts.append(f"({chunk_clause})")
            queries.append(" ".join(chunk_parts))

    return queries


def _search_duckduckgo_sync(query: str, max_results: int = 20) -> list[dict]:
    """Search DuckDuckGo using Playwright. No CAPTCHAs, no blocking."""
    results = []

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                channel="chrome",
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
        context.set_default_timeout(15000)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()

        try:
            url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.0, 3.5))

            # Scroll and click "More Results" to load additional results
            for _ in range(3):
                page.keyboard.press("End")
                time.sleep(1.0)
                try:
                    more_btn = page.locator("button:has-text('More results'), button:has-text('More Results'), a:has-text('More results')")
                    if more_btn.count() > 0:
                        more_btn.first.click()
                        time.sleep(random.uniform(1.5, 2.5))
                except Exception:
                    pass

            # DuckDuckGo result extraction
            result_links = page.locator("a[href*='linkedin.com/in/']")
            count = result_links.count()
            seen_hrefs: set[str] = set()

            for i in range(count):
                if len(results) >= max_results:
                    break
                try:
                    el = result_links.nth(i)
                    href = el.get_attribute("href") or ""
                    if "linkedin.com/in/" not in href:
                        continue

                    clean_href = re.sub(r"\?.*$", "", href)
                    if clean_href in seen_hrefs:
                        continue
                    seen_hrefs.add(clean_href)

                    text = el.inner_text().strip()

                    # Try to get snippet from the parent result container
                    snippet = ""
                    try:
                        article = el.locator("xpath=ancestor::article").first
                        if article.count() > 0:
                            snippet_el = article.locator("div[data-result='snippet']").first
                            if snippet_el.count() > 0:
                                snippet = snippet_el.inner_text().strip()
                    except Exception:
                        pass

                    if not snippet:
                        try:
                            parent = el.locator("xpath=..").first
                            sibling = parent.locator("xpath=following-sibling::*").first
                            if sibling.count() > 0:
                                snippet = sibling.inner_text().strip()[:200]
                        except Exception:
                            pass

                    results.append({
                        "link": clean_href,
                        "title": text if text else "",
                        "snippet": snippet,
                    })
                except Exception:
                    continue

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
        finally:
            browser.close()

    return results


def parse_linkedin_result(item: dict) -> LinkedInProfile | None:
    """Parse a search result into a LinkedInProfile."""
    link = item.get("link", "")
    if "linkedin.com/in/" not in link:
        return None

    title = item.get("title", "")
    snippet = item.get("snippet", "")

    if not title or title.startswith("http"):
        return _parse_url_into_profile(link, snippet)

    # Clean common LinkedIn title patterns: "Name - Title - Company | LinkedIn"
    name = title.split(" - ")[0].strip() if " - " in title else title.split("|")[0].strip()
    name = re.sub(r"\s*\|.*$", "", name)
    name = re.sub(r"\s*–.*$", "", name)
    name = re.sub(r"\s*LinkedIn\s*$", "", name, flags=re.IGNORECASE).strip()

    if not name:
        return _parse_url_into_profile(link, snippet)

    headline = None
    if " - " in title:
        parts = title.split(" - ")
        if len(parts) >= 2:
            headline = parts[1].strip()
            headline = re.sub(r"\s*\|.*$", "", headline)
            headline = re.sub(r"\s*–.*$", "", headline)
            headline = re.sub(r"\s*LinkedIn\s*$", "", headline, flags=re.IGNORECASE).strip()

    location = None
    loc_match = re.search(
        r"(?:located?\s+in|based\s+in|from)\s+([A-Z][^.·\-|]+)",
        snippet,
        re.IGNORECASE,
    )
    if loc_match:
        location = loc_match.group(1).strip()

    linkedin_url = re.sub(r"\?.*$", "", link)

    return LinkedInProfile(
        name=name,
        headline=headline,
        location=location,
        linkedin_url=linkedin_url,
        snippet=snippet.strip() if snippet else None,
    )


def _parse_url_into_profile(url: str, snippet: str = "") -> LinkedInProfile | None:
    """Extract name from a LinkedIn profile URL as fallback."""
    if "linkedin.com/in/" not in url:
        return None

    clean_url = re.sub(r"\?.*$", "", url)
    slug = clean_url.rstrip("/").split("/")[-1]
    name = slug.replace("-", " ").title()
    name = re.sub(r"\s+\d+$", "", name)
    name = re.sub(r"\s+[a-f0-9]{6,}$", "", name, flags=re.IGNORECASE)

    return LinkedInProfile(
        name=name,
        headline=None,
        location=None,
        linkedin_url=clean_url,
        snippet=snippet.strip() if snippet else None,
    )


async def search_linkedin_profiles(
    query: str,
    api_key: str = "",
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
    alternative_terms: list[str] | None = None,
    max_results: int = 20,
) -> tuple[list[LinkedInProfile], str]:
    """Search for LinkedIn profiles using Playwright + DuckDuckGo."""
    rate_error = _check_rate_limit()
    if rate_error:
        raise Exception(rate_error)

    # Build queries for main terms + alternatives
    search_queries = build_search_queries(query, location, companies, seniority)
    if alternative_terms:
        for alt in alternative_terms[:2]:
            search_queries.extend(build_search_queries(alt, location, companies, seniority))

    profiles: list[LinkedInProfile] = []
    seen_urls: set[str] = set()
    loop = asyncio.get_event_loop()

    for sq in search_queries:
        if len(profiles) >= max_results:
            break

        remaining = max_results - len(profiles)
        items = await loop.run_in_executor(_executor, _search_duckduckgo_sync, sq, remaining)

        for item in items:
            profile = parse_linkedin_result(item)
            if profile and profile.linkedin_url not in seen_urls:
                seen_urls.add(profile.linkedin_url)
                profiles.append(profile)

        if len(search_queries) > 1:
            await asyncio.sleep(random.uniform(1.5, 3.0))

    return profiles[:max_results], search_queries[0]
