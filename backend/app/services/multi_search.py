"""Multi-source LinkedIn profile search.

Searches DuckDuckGo, Bing, Google, and Brave in parallel, then merges
results. Each source returns different snippet data, so combining them
gives the AI much richer context for scoring.
"""

import asyncio
import random
import re
import time
from concurrent.futures import ThreadPoolExecutor
from collections import deque
from dataclasses import dataclass, field as dc_field

import httpx
from playwright.sync_api import sync_playwright, Browser, BrowserContext

_executor = ThreadPoolExecutor(max_workers=5)

_search_timestamps: deque[float] = deque()
MAX_SEARCHES_PER_HOUR = 10

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
window.chrome = {runtime: {}};
"""

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _check_rate_limit() -> str | None:
    now = time.time()
    while _search_timestamps and _search_timestamps[0] < now - 3600:
        _search_timestamps.popleft()
    if len(_search_timestamps) >= MAX_SEARCHES_PER_HOUR:
        oldest = _search_timestamps[0]
        wait_minutes = int((oldest + 3600 - now) / 60) + 1
        return f"Rate limit reached ({MAX_SEARCHES_PER_HOUR}/hr). Try again in ~{wait_minutes} min."
    _search_timestamps.append(now)
    return None


def _normalize_linkedin_url(url: str) -> str:
    """Normalize a LinkedIn profile URL for deduplication."""
    url = re.sub(r"\?.*$", "", url)
    url = url.rstrip("/")
    url = re.sub(r"^https?://(www\.)?", "https://www.", url)
    for prefix in ["/en", "/fr", "/de", "/es", "/pt", "/in"]:
        if url.count("/in/") > 1:
            break
    return url.lower()


def _extract_linkedin_url(href: str) -> str | None:
    """Extract and clean a LinkedIn profile URL from a search result link."""
    if "linkedin.com/in/" not in href:
        return None
    match = re.search(r"https?://[a-z]{0,3}\.?linkedin\.com/in/[^?&#\s]+", href)
    if match:
        return re.sub(r"\?.*$", "", match.group(0))
    return None


@dataclass
class RawResult:
    """A single search result from one source."""
    linkedin_url: str
    title: str = ""
    snippet: str = ""
    full_text: str = ""
    source: str = ""


@dataclass
class MergedProfile:
    """Profile data merged from multiple search sources."""
    linkedin_url: str
    name: str = ""
    headline: str | None = None
    location: str | None = None
    snippets: list[str] = dc_field(default_factory=list)
    sources: list[str] = dc_field(default_factory=list)
    experience_text: str | None = None
    education_text: str | None = None
    # Enrichment data
    scholar_data: dict | None = None
    orcid_data: dict | None = None
    web_bio_data: dict | None = None
    about_text: str | None = None
    public_page_data: dict = dc_field(default_factory=dict)


def _create_browser_context(playwright_instance) -> tuple:
    """Create a browser and context with stealth settings."""
    try:
        browser = playwright_instance.chromium.launch(
            headless=True,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
        )
    except Exception:
        browser = playwright_instance.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent=USER_AGENT,
        locale="en-US",
        viewport={"width": 1366, "height": 768},
    )
    context.set_default_timeout(12000)
    context.add_init_script(STEALTH_JS)
    return browser, context


# ---------------------------------------------------------------------------
# Source: DuckDuckGo
# ---------------------------------------------------------------------------

def _search_duckduckgo(query: str, max_results: int = 25) -> list[RawResult]:
    import urllib.parse
    results = []
    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        page = context.new_page()
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://duckduckgo.com/?q={encoded}"
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.0, 3.0))

            # Scroll aggressively for more results
            for _ in range(3):
                page.keyboard.press("End")
                time.sleep(0.5)

            # Click "More Results" button
            try:
                more = page.locator("button", has_text=re.compile(r"More\s+Results", re.IGNORECASE))
                if more.count() > 0:
                    more.first.click()
                    time.sleep(1.5)
                    for _ in range(2):
                        page.keyboard.press("End")
                        time.sleep(0.5)
            except Exception:
                pass

            articles = page.locator("article")
            seen: set[str] = set()
            for i in range(articles.count()):
                if len(results) >= max_results:
                    break
                try:
                    article = articles.nth(i)
                    link_el = article.locator("a[href*='linkedin.com/in/']").first
                    if link_el.count() == 0:
                        continue
                    href = link_el.get_attribute("href") or ""
                    li_url = _extract_linkedin_url(href)
                    if not li_url or _normalize_linkedin_url(li_url) in seen:
                        continue
                    seen.add(_normalize_linkedin_url(li_url))

                    text = article.inner_text().strip()
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    title = ""
                    snippet = ""
                    for line in lines:
                        if ("linkedin" in line.lower() and " - " in line) or "| LinkedIn" in line:
                            title = line.replace(" | LinkedIn", "").strip()
                        elif len(line) > 40 and "linkedin" not in line.lower() and "http" not in line.lower():
                            if not snippet:
                                snippet = line
                    if not title:
                        for line in lines:
                            if " - " in line and "linkedin" not in line.lower() and "http" not in line.lower():
                                title = line
                                break

                    results.append(RawResult(
                        linkedin_url=li_url, title=title,
                        snippet=snippet, full_text=text[:600], source="duckduckgo",
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[DDG] search error: {e}")
        finally:
            browser.close()
    return results


# ---------------------------------------------------------------------------
# Source: Bing
# ---------------------------------------------------------------------------

def _search_yahoo(query: str, max_results: int = 25) -> list[RawResult]:
    """Yahoo Search (Bing-powered)."""
    import urllib.parse
    results = []
    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        page = context.new_page()
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://search.yahoo.com/search?p={encoded}&n=30"
            page.goto(url, wait_until="domcontentloaded", timeout=12000)
            time.sleep(random.uniform(1.5, 2.5))

            all_links = page.locator("a[href*='linkedin.com/in/']")
            seen: set[str] = set()

            for i in range(all_links.count()):
                if len(results) >= max_results:
                    break
                try:
                    link = all_links.nth(i)
                    href = link.get_attribute("href") or ""
                    li_match = re.search(r"https?://[a-z]{0,3}\.?linkedin\.com/in/[^?&#\s]+", href)
                    if not li_match:
                        continue
                    li_url = re.sub(r"\?.*$", "", li_match.group(0))
                    if _normalize_linkedin_url(li_url) in seen:
                        continue
                    seen.add(_normalize_linkedin_url(li_url))

                    title = ""
                    snippet = ""
                    full_text = ""
                    try:
                        parent = link.locator("xpath=ancestor::div[contains(@class,'algo') or contains(@class,'dd') or contains(@class,'result') or contains(@class,'Sr')]")
                        if parent.count() > 0:
                            # Yahoo uses h3 for the title
                            h3 = parent.first.locator("h3").first
                            if h3.count() > 0:
                                title = h3.inner_text().strip()
                            full_text = parent.first.inner_text().strip()
                            for line in full_text.split("\n"):
                                line = line.strip()
                                if len(line) > 50 and "linkedin" not in line.lower() and "http" not in line.lower():
                                    snippet = line
                                    break
                    except Exception:
                        pass

                    # Fallback: clean link text
                    if not title or "linkedin" in title.lower():
                        raw = link.inner_text().strip()
                        for line in raw.split("\n"):
                            line = line.strip()
                            if line and "linkedin" not in line.lower() and "http" not in line.lower() and len(line) > 5:
                                title = line
                                break

                    if not title:
                        continue

                    results.append(RawResult(
                        linkedin_url=li_url, title=title,
                        snippet=snippet, full_text=full_text[:600], source="yahoo",
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[Yahoo] search error: {e}")
        finally:
            browser.close()
    return results


# ---------------------------------------------------------------------------
# Source: Google
# ---------------------------------------------------------------------------

def _search_startpage(query: str, max_results: int = 25) -> list[RawResult]:
    """Startpage (Google proxy, no CAPTCHAs, no tracking)."""
    import urllib.parse
    results = []
    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        page = context.new_page()
        try:
            encoded = urllib.parse.quote_plus(query)
            url = f"https://www.startpage.com/do/dsearch?query={encoded}"
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(1.5, 2.5))

            # Startpage uses article or section.result containers
            items = page.locator("article, section.result, div.result")
            seen: set[str] = set()

            for i in range(items.count()):
                if len(results) >= max_results:
                    break
                try:
                    item = items.nth(i)
                    link_el = item.locator("a[href*='linkedin.com/in/']").first
                    if link_el.count() == 0:
                        continue
                    href = link_el.get_attribute("href") or ""
                    li_url = _extract_linkedin_url(href)
                    if not li_url or _normalize_linkedin_url(li_url) in seen:
                        continue
                    seen.add(_normalize_linkedin_url(li_url))

                    title_el = item.locator("h2, h3").first
                    title = title_el.inner_text().strip() if title_el.count() > 0 else ""

                    snippet = ""
                    full_text = item.inner_text().strip()
                    for line in full_text.split("\n"):
                        line = line.strip()
                        if len(line) > 50 and "linkedin" not in line.lower() and "http" not in line.lower():
                            snippet = line
                            break

                    results.append(RawResult(
                        linkedin_url=li_url, title=title,
                        snippet=snippet, full_text=full_text[:600], source="startpage",
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[Startpage] search error: {e}")
        finally:
            browser.close()
    return results


# ---------------------------------------------------------------------------
# Source: Brave Search
# ---------------------------------------------------------------------------

def _search_brave(query: str, max_results: int = 25) -> list[RawResult]:
    results = []
    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        page = context.new_page()
        try:
            url = f"https://search.brave.com/search?q={query.replace(' ', '+')}"
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.0, 3.0))

            # Check for CAPTCHA
            if "captcha" in page.title().lower() or "not a robot" in page.content()[:500].lower():
                print("[Brave] CAPTCHA detected, skipping")
                browser.close()
                return results

            # Brave uses #results with various child elements
            # Try broad selector to catch all result items
            items = page.locator("#results > div")
            seen: set[str] = set()
            for i in range(items.count()):
                if len(results) >= max_results:
                    break
                try:
                    item = items.nth(i)
                    link_el = item.locator("a[href*='linkedin.com/in/']").first
                    if link_el.count() == 0:
                        continue
                    href = link_el.get_attribute("href") or ""
                    li_url = _extract_linkedin_url(href)
                    if not li_url or _normalize_linkedin_url(li_url) in seen:
                        continue
                    seen.add(_normalize_linkedin_url(li_url))

                    full_text = item.inner_text().strip()
                    lines = [l.strip() for l in full_text.split("\n") if l.strip()]

                    # Extract title -- look for "Name - Headline" pattern in text
                    title = ""
                    snippet = ""
                    for line in lines:
                        if " - " in line and "linkedin" not in line.lower() and "http" not in line.lower() and len(line) > 10:
                            title = line
                            break
                        if "| LinkedIn" in line:
                            title = line.replace("| LinkedIn", "").strip()
                            break
                    # If no title from text, build from snippet
                    if not title:
                        for line in lines:
                            if len(line) > 30 and "linkedin" not in line.lower() and "http" not in line.lower() and ">" not in line:
                                title = line
                                break

                    for line in lines:
                        if len(line) > 50 and "linkedin" not in line.lower() and "http" not in line.lower() and line != title and ">" not in line:
                            snippet = line
                            break

                    results.append(RawResult(
                        linkedin_url=li_url, title=title,
                        snippet=snippet, full_text=full_text[:600], source="brave",
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[Brave] search error: {e}")
        finally:
            browser.close()
    return results


# ---------------------------------------------------------------------------
# LinkedIn Public Profile Fetcher (no login required)
# ---------------------------------------------------------------------------

def _fetch_linkedin_chunk(urls: list[str]) -> dict[str, dict]:
    """Fetch a chunk of LinkedIn pages in one browser instance."""
    data: dict[str, dict] = {}
    if not urls:
        return data

    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        context.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf,eot,mp4,webm,ico}", lambda route: route.abort())
        context.route("**/analytics/**", lambda route: route.abort())
        context.route("**/tracking/**", lambda route: route.abort())

        for url in urls:
            try:
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=8000)

                page_data: dict = {}

                og_title = page.locator('meta[property="og:title"]').first
                if og_title.count() > 0:
                    page_data["og_title"] = og_title.get_attribute("content") or ""

                og_desc = page.locator('meta[property="og:description"]').first
                if og_desc.count() > 0:
                    page_data["og_description"] = og_desc.get_attribute("content") or ""

                meta_desc = page.locator('meta[name="description"]').first
                if meta_desc.count() > 0:
                    page_data["meta_description"] = meta_desc.get_attribute("content") or ""

                # Extract visible body text for experience/education/location
                try:
                    body_text = page.locator("body").inner_text(timeout=3000)
                    if body_text and len(body_text) > 100:
                        # LinkedIn auth walls have very little content
                        low = body_text.lower()
                        if "sign in" not in low[:200] or len(body_text) > 1000:
                            page_data["body_text"] = body_text[:4000]
                except Exception:
                    pass

                if page_data:
                    data[_normalize_linkedin_url(url)] = page_data

                page.close()
            except Exception:
                try:
                    page.close()
                except Exception:
                    pass

        browser.close()
    return data


def _fetch_linkedin_public_pages(urls: list[str]) -> dict[str, dict]:
    """Fetch LinkedIn public profile pages using parallel browser instances.
    Splits URLs across multiple threads, each with its own browser.
    """
    if not urls:
        return {}

    NUM_WORKERS = 4
    chunk_size = max(1, len(urls) // NUM_WORKERS + 1)
    chunks = [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

    data: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as pool:
        futures = [pool.submit(_fetch_linkedin_chunk, chunk) for chunk in chunks]
        for future in futures:
            try:
                chunk_data = future.result(timeout=30)
                data.update(chunk_data)
            except Exception:
                continue

    return data


# ---------------------------------------------------------------------------
# Parse and extract structured data from raw text
# ---------------------------------------------------------------------------

def _name_from_url_slug(url: str) -> str:
    """Extract a human-readable name from a LinkedIn profile URL slug."""
    slug = url.rstrip("/").split("/")[-1]
    name = slug.replace("-", " ").title()
    # Remove trailing IDs and hashes
    name = re.sub(r"\s+\d+$", "", name)
    name = re.sub(r"\s+[A-Fa-f0-9]{6,}[A-Za-z]?\s*$", "", name)
    # Remove common LinkedIn URL suffixes
    name = re.sub(r"\s+\d{4,}\s*$", "", name)
    return name.strip()


def _parse_name_from_title(title: str) -> str:
    """Extract the person's name from a search result title."""
    name = title.split(" - ")[0].strip() if " - " in title else title.split("|")[0].strip()
    name = re.sub(r"\s*\|.*$", "", name)
    name = re.sub(r"\s*–.*$", "", name)
    name = re.sub(r"\s*LinkedIn\s*$", "", name, flags=re.IGNORECASE).strip()
    # Remove trailing hex-like IDs from Brave results (e.g. "John Smith B7228619A")
    name = re.sub(r"\s+[A-Fa-f0-9]{6,}[A-Za-z]?\s*$", "", name).strip()
    # Remove trailing random digit strings
    name = re.sub(r"\s+\d{4,}\s*$", "", name).strip()
    return name


def _parse_headline_from_title(title: str) -> str | None:
    if " - " not in title:
        return None
    parts = title.split(" - ")
    if len(parts) >= 2:
        headline = parts[1].strip()
        headline = re.sub(r"\s*\|.*$", "", headline)
        headline = re.sub(r"\s*–.*$", "", headline)
        headline = re.sub(r"\s*LinkedIn\s*$", "", headline, flags=re.IGNORECASE).strip()
        return headline if headline else None
    return None


def _extract_location(text: str) -> str | None:
    m = re.search(r"Location:\s*([^·\n]+)", text, re.IGNORECASE)
    if m:
        loc = m.group(1).strip()
        loc = re.sub(r"\s*·.*$", "", loc).strip()
        loc = re.sub(r"\.\s*\d+\+?\s*connections.*$", "", loc, flags=re.IGNORECASE).strip()
        if loc and len(loc) < 60:
            return loc
    m = re.search(r"(?:located?\s+in|based\s+in|from)\s+([A-Z][^.·\-|\n]{3,40})", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _extract_experience(text: str) -> str | None:
    m = re.search(r"Experience:?\s*(.+?)(?:\s*·\s*Education|$)", text, re.IGNORECASE)
    if m:
        exp = m.group(1).strip()
        # Clean trailing location/connections boilerplate
        exp = re.sub(r"\s*·\s*Location:.*$", "", exp).strip()
        exp = re.sub(r"\s*\d+\+?\s*connections.*$", "", exp, flags=re.IGNORECASE).strip()
        return exp[:300] if exp else None
    return None


def _extract_education(text: str) -> str | None:
    m = re.search(r"Education:?\s*(.+?)(?:\s*·\s*Location|\s*·\s*\d|$)", text, re.IGNORECASE)
    return m.group(1).strip()[:200] if m else None


def _extract_location_from_body(body: str) -> str | None:
    """Extract location from LinkedIn page body text."""
    lines = body.split("\n")
    for i, line in enumerate(lines):
        line = line.strip()
        # LinkedIn format: "City, State, Country  Contact Info"
        m = re.match(r"^([A-Z][a-zA-Z. ]+,\s*[A-Za-z ]+(?:,\s*[A-Za-z ]+)?)\s*(?:Contact Info|$)", line)
        if m:
            loc = m.group(1).strip().rstrip(",")
            # Validate it's not a menu item
            if len(loc) > 5 and len(loc) < 80:
                return loc
        # "Greater X Area" or "X Bay Area" or "X Metropolitan Area"
        if re.match(r"^(Greater\s+)?[A-Z][a-zA-Z. ]+(Bay\s+Area|Metropolitan\s+Area|Area)\s*$", line):
            return line.strip()
    return None


def _extract_experience_from_body(body: str) -> str | None:
    """Extract recent experience from LinkedIn page body text."""
    lines = body.split("\n")
    in_exp = False
    exp_items = []
    for line in lines:
        line = line.strip()
        if line.lower() == "experience":
            in_exp = True
            continue
        if in_exp:
            if line.lower() in ("education", "skills", "licenses & certifications",
                                 "volunteer experience", "courses", "honors & awards",
                                 "languages", "interests", "recommendations", "activity"):
                break
            if len(line) > 3 and not line.startswith("Show "):
                exp_items.append(line)
                if len(exp_items) >= 6:
                    break
    if exp_items:
        return " · ".join(exp_items[:6])[:300]
    return None


def _extract_education_from_body(body: str) -> str | None:
    """Extract education from LinkedIn page body text."""
    lines = body.split("\n")
    in_edu = False
    edu_items = []
    for line in lines:
        line = line.strip()
        if line.lower() == "education":
            in_edu = True
            continue
        if in_edu:
            if line.lower() in ("skills", "licenses & certifications",
                                 "volunteer experience", "courses", "honors & awards",
                                 "languages", "interests", "recommendations", "activity"):
                break
            if len(line) > 3 and not line.startswith("Show "):
                edu_items.append(line)
                if len(edu_items) >= 4:
                    break
    if edu_items:
        return " · ".join(edu_items[:4])[:200]
    return None


def _parse_public_page(page_data: dict) -> dict:
    """Extract structured info from LinkedIn public page metadata."""
    import html as _html
    info: dict = {}

    og_desc = _html.unescape(page_data.get("og_description", "") or "")
    meta_desc = _html.unescape(page_data.get("meta_description", "") or "")
    og_title = _html.unescape(page_data.get("og_title", "") or "")

    # og:description often has: "Role at Company · Experience: X · Education: Y · Location: Z · 500+ connections"
    best_desc = og_desc if len(og_desc) > len(meta_desc) else meta_desc

    if best_desc:
        info["description"] = best_desc

        exp = _extract_experience(best_desc)
        if exp:
            info["experience_text"] = exp

        edu = _extract_education(best_desc)
        if edu:
            info["education_text"] = edu

        loc = _extract_location(best_desc)
        if loc:
            info["location"] = loc

        # First line is usually "Headline · Company"
        first_part = best_desc.split("·")[0].strip() if "·" in best_desc else ""
        if first_part and len(first_part) > 5:
            info["headline_from_meta"] = first_part

    if og_title:
        info["og_title"] = og_title

    # Parse body text for additional data when meta tags are incomplete
    body = page_data.get("body_text", "")
    if body and len(body) > 100:
        info["visible_text"] = body[:800]

        # Extract location from body if not found in meta
        if not info.get("location"):
            loc = _extract_location_from_body(body)
            if loc:
                info["location"] = loc

        # Extract experience from body if not found in meta
        if not info.get("experience_text"):
            exp = _extract_experience_from_body(body)
            if exp:
                info["experience_text"] = exp

        # Extract education from body if not found in meta
        if not info.get("education_text"):
            edu = _extract_education_from_body(body)
            if edu:
                info["education_text"] = edu

    return info


# ---------------------------------------------------------------------------
# Merge results from all sources
# ---------------------------------------------------------------------------

def _merge_results(
    all_results: list[list[RawResult]],
    public_pages: dict[str, dict],
) -> list[MergedProfile]:
    """Merge raw results from multiple sources into deduplicated rich profiles."""
    profiles_by_url: dict[str, MergedProfile] = {}

    for source_results in all_results:
        for r in source_results:
            key = _normalize_linkedin_url(r.linkedin_url)

            if key not in profiles_by_url:
                name = _parse_name_from_title(r.title)
                headline = _parse_headline_from_title(r.title)

                # If name looks like a job title/role rather than a person name, swap
                job_words = {
                    "director", "manager", "vp", "associate", "senior", "lead",
                    "head", "chief", "president", "postdoc", "professor", "analyst",
                    "consultant", "engineer", "scientist", "researcher", "intern",
                    "coordinator", "specialist", "advisor", "fellow", "officer",
                    "founder", "partner", "principal", "staff", "supervisor",
                }
                name_lower = name.lower() if name else ""
                looks_like_title = (
                    (any(w in name_lower for w in job_words) and len(name.split()) > 2)
                    or "@" in name
                    or name_lower.startswith("the ")
                )
                if name and looks_like_title:
                    if not headline:
                        headline = name
                    name = _name_from_url_slug(r.linkedin_url)

                if not name or name.startswith("http"):
                    name = _name_from_url_slug(r.linkedin_url)

                profiles_by_url[key] = MergedProfile(
                    linkedin_url=r.linkedin_url,
                    name=name,
                    headline=headline,
                )

            profile = profiles_by_url[key]

            if r.source not in profile.sources:
                profile.sources.append(r.source)

            # Merge headline (prefer longer)
            new_headline = _parse_headline_from_title(r.title)
            if new_headline and (not profile.headline or len(new_headline) > len(profile.headline)):
                profile.headline = new_headline

            # Collect unique snippets from each source
            combined_text = f"{r.snippet} {r.full_text}".strip()
            if combined_text and combined_text not in profile.snippets:
                # Only add if it has substantial new info
                is_new = True
                for existing in profile.snippets:
                    if combined_text[:80] in existing or existing[:80] in combined_text:
                        # Similar content, keep the longer one
                        if len(combined_text) > len(existing):
                            profile.snippets.remove(existing)
                        else:
                            is_new = False
                        break
                if is_new:
                    profile.snippets.append(combined_text[:500])

            # Extract location from any source text
            if not profile.location:
                loc = _extract_location(combined_text)
                if loc:
                    # Clean LinkedIn boilerplate from location
                    loc = re.sub(r"\s*\.{3,}.*$", "", loc).strip()
                    loc = re.sub(r"\s*\d+\+?\s*connections.*$", "", loc, flags=re.IGNORECASE).strip()
                    loc = re.sub(r"\s*on\s+LinkedIn.*$", "", loc, flags=re.IGNORECASE).strip()
                    if loc and len(loc) < 60:
                        profile.location = loc

            # Extract experience/education from any source
            if not profile.experience_text:
                exp = _extract_experience(combined_text)
                if exp:
                    profile.experience_text = exp

            if not profile.education_text:
                edu = _extract_education(combined_text)
                if edu:
                    profile.education_text = edu

    # Merge in public page data
    for key, profile in profiles_by_url.items():
        if key in public_pages:
            page_info = _parse_public_page(public_pages[key])
            profile.public_page_data = page_info

            # Use og:title for a cleaner name (e.g. "Samuel Crawford - Director, US HEOR | LinkedIn")
            og_title = page_info.get("og_title", "")
            skip_titles = {"sign up", "sign in", "log in", "linkedin"}
            if og_title and " - " in og_title and og_title.split(" - ")[0].strip().lower() not in skip_titles:
                clean_name = og_title.split(" - ")[0].strip()
                # Only use if it looks like a real name (2-5 words, no IDs)
                if clean_name and 1 < len(clean_name.split()) <= 5 and not re.search(r"[0-9]{3,}", clean_name):
                    profile.name = clean_name
                    # Also extract headline from og_title if present
                    og_parts = og_title.replace("| LinkedIn", "").split(" - ", 1)
                    if len(og_parts) >= 2:
                        og_headline = og_parts[1].strip()
                        if og_headline and (not profile.headline or len(og_headline) > len(profile.headline)):
                            profile.headline = og_headline

            if not profile.headline and page_info.get("headline_from_meta"):
                profile.headline = page_info["headline_from_meta"]

            if not profile.location and page_info.get("location"):
                profile.location = page_info["location"]

            if not profile.experience_text and page_info.get("experience_text"):
                profile.experience_text = page_info["experience_text"]

            if not profile.education_text and page_info.get("education_text"):
                profile.education_text = page_info["education_text"]

            if page_info.get("description"):
                profile.snippets.append(f"[LinkedIn] {page_info['description'][:400]}")

            if page_info.get("visible_text"):
                profile.snippets.append(f"[LinkedIn Page] {page_info['visible_text'][:400]}")

            if "linkedin_public" not in profile.sources:
                profile.sources.append("linkedin_public")

    # Sort: profiles found in more sources first, then alphabetically
    merged = list(profiles_by_url.values())
    merged.sort(key=lambda p: (-len(p.sources), p.name))

    return merged


# ---------------------------------------------------------------------------
# Build search queries
# ---------------------------------------------------------------------------

def build_search_queries(
    query: str,
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
) -> list[str]:
    base = "site:linkedin.com/in"
    parts = [base, query]
    if location:
        parts.append(f'"{location}"')
    if seniority:
        parts.append(f'"{seniority}"')
    if companies:
        clause = " OR ".join(f'"{c}"' for c in companies)
        parts.append(f"({clause})")

    queries = [" ".join(parts)]

    # Add a broader version without quoted location for better coverage
    # Use key words from the query to stay relevant
    if location:
        broad_parts = [base, query, location]
        if seniority:
            broad_parts.append(f'"{seniority}"')
        queries.append(" ".join(broad_parts))

        # Also add a focused HEOR-specific query if HEOR-related terms are present
        heor_terms = ["heor", "health economics", "outcomes research", "rwe", "real world evidence",
                      "market access", "medical affairs"]
        query_lower = query.lower()
        if any(term in query_lower for term in heor_terms):
            queries.append(f'{base} HEOR "health economics" pharma biotech {location}')

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


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def search_linkedin_profiles_multi(
    query: str,
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
    alternative_terms: list[str] | None = None,
    max_results: int = 30,
) -> tuple[list[MergedProfile], str]:
    """Search for LinkedIn profiles across multiple search engines simultaneously.

    Returns merged, deduplicated profiles with combined data from all sources.
    """
    rate_error = _check_rate_limit()
    if rate_error:
        raise Exception(rate_error)

    search_queries = build_search_queries(query, location, companies, seniority)
    primary_query = search_queries[0]

    # Build the full query string for all sources
    all_queries = list(search_queries)
    if alternative_terms:
        for alt in alternative_terms[:2]:
            all_queries.extend(build_search_queries(alt, location, companies, seniority))

    # For each source, we'll concatenate queries or use the primary one
    # Each source gets the same primary query for consistency
    loop = asyncio.get_event_loop()

    # Build both primary and broad queries
    broad_query = search_queries[1] if len(search_queries) > 1 else None

    print(f"[MultiSearch] Launching parallel searches across engines...")
    start_time = time.time()

    # Run all engines in parallel with BOTH primary and broad queries
    # Primary: quoted location for precision. Broad: unquoted for coverage.
    futures = {
        "DDG": loop.run_in_executor(_executor, _search_duckduckgo, primary_query, max_results),
        "Startpage": loop.run_in_executor(_executor, _search_startpage, primary_query, max_results),
        "Yahoo": loop.run_in_executor(_executor, _search_yahoo, primary_query, max_results),
        "Brave": loop.run_in_executor(_executor, _search_brave, primary_query, max_results),
    }
    # Run additional queries for broader coverage
    if broad_query:
        futures["DDG-broad"] = loop.run_in_executor(_executor, _search_duckduckgo, broad_query, max_results)
    # If there's a focused HEOR query, run it on Startpage
    if len(search_queries) > 2:
        futures["Startpage-HEOR"] = loop.run_in_executor(_executor, _search_startpage, search_queries[2], max_results)

    results_map = {}
    gathered = await asyncio.gather(*futures.values(), return_exceptions=True)
    for (name, _), result in zip(futures.items(), gathered):
        results_map[name] = result

    all_source_results: list[list[RawResult]] = []
    for name in futures:
        result = results_map[name]
        if isinstance(result, Exception):
            print(f"[MultiSearch] {name} failed: {result}")
            all_source_results.append([])
        else:
            print(f"[MultiSearch] {name}: {len(result)} results")
            all_source_results.append(result)

    elapsed = time.time() - start_time
    print(f"[MultiSearch] All searches completed in {elapsed:.1f}s")

    # If coverage is still low, run Startpage with broad query too
    total_raw = sum(len(r) for r in all_source_results)
    if broad_query and total_raw < 20:
        print(f"[MultiSearch] Running extra broad search (only {total_raw} results so far)...")
        extra = await loop.run_in_executor(_executor, _search_startpage, broad_query, max_results)
        if not isinstance(extra, Exception) and extra:
            all_source_results.append(extra)
            print(f"[MultiSearch] Startpage-broad: {len(extra)} results")

    # Alternative term searches
    if alternative_terms:
        alt_futures = []
        for alt in alternative_terms[:2]:
            alt_q = build_search_queries(alt, location, companies, seniority)[0]
            alt_futures.append(loop.run_in_executor(_executor, _search_duckduckgo, alt_q, 15))
            alt_futures.append(loop.run_in_executor(_executor, _search_yahoo, alt_q, 10))

        alt_results_list = await asyncio.gather(*alt_futures, return_exceptions=True)
        for i, alt_r in enumerate(alt_results_list):
            if not isinstance(alt_r, Exception) and alt_r:
                all_source_results.append(alt_r)
                print(f"[MultiSearch] Alt search #{i+1}: {len(alt_r)} results")

    # Collect all unique LinkedIn URLs for public page fetching
    all_urls: set[str] = set()
    for source_results in all_source_results:
        for r in source_results:
            all_urls.add(r.linkedin_url)

    # Fetch LinkedIn public pages (no login) for richer data
    url_list = list(all_urls)[:max_results]
    print(f"[MultiSearch] Fetching {len(url_list)} LinkedIn public pages (no login)...")
    public_start = time.time()
    public_pages = await loop.run_in_executor(_executor, _fetch_linkedin_public_pages, url_list)
    public_elapsed = time.time() - public_start
    print(f"[MultiSearch] Public pages fetched in {public_elapsed:.1f}s, got data for {len(public_pages)}")

    # Merge and deduplicate
    merged = _merge_results(all_source_results, public_pages)
    print(f"[MultiSearch] Merged to {len(merged)} unique profiles (from {sum(len(r) for r in all_source_results)} raw results)")

    return merged[:max_results], primary_query
