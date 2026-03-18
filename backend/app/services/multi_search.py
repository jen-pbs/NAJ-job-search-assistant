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
    results = []
    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        page = context.new_page()
        try:
            url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.0, 3.5))

            for _ in range(3):
                page.keyboard.press("End")
                time.sleep(0.8)
                try:
                    more = page.locator("button:has-text('More results'), button:has-text('More Results'), a:has-text('More results')")
                    if more.count() > 0:
                        more.first.click()
                        time.sleep(random.uniform(1.0, 2.0))
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

def _search_bing(query: str, max_results: int = 25) -> list[RawResult]:
    results = []
    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        page = context.new_page()
        try:
            url = f"https://www.bing.com/search?q={query.replace(' ', '+')}&count=30"
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.5, 4.0))

            for _ in range(2):
                page.keyboard.press("End")
                time.sleep(1.0)

            # Extract all links from the page that point to LinkedIn profiles
            all_links = page.locator("a[href*='linkedin.com/in/']")
            seen: set[str] = set()
            link_count = all_links.count()

            for i in range(link_count):
                if len(results) >= max_results:
                    break
                try:
                    link = all_links.nth(i)
                    href = link.get_attribute("href") or ""
                    li_url = _extract_linkedin_url(href)
                    if not li_url or _normalize_linkedin_url(li_url) in seen:
                        continue
                    seen.add(_normalize_linkedin_url(li_url))

                    # Walk up to the containing result element
                    title = link.inner_text().strip()

                    # Try to get the parent container's text for snippet
                    snippet = ""
                    full_text = ""
                    try:
                        parent = page.locator(f"li:has(a[href*='{li_url.split('/in/')[1]}'])")
                        if parent.count() > 0:
                            full_text = parent.first.inner_text().strip()
                            for line in full_text.split("\n"):
                                line = line.strip()
                                if len(line) > 50 and "linkedin" not in line.lower() and "http" not in line.lower():
                                    snippet = line
                                    break
                    except Exception:
                        pass

                    results.append(RawResult(
                        linkedin_url=li_url, title=title,
                        snippet=snippet, full_text=full_text[:600], source="bing",
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[Bing] search error: {e}")
        finally:
            browser.close()
    return results


# ---------------------------------------------------------------------------
# Source: Google
# ---------------------------------------------------------------------------

def _search_google(query: str, max_results: int = 25) -> list[RawResult]:
    results = []
    with sync_playwright() as p:
        browser, context = _create_browser_context(p)
        page = context.new_page()
        try:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num=30"
            page.goto(url, wait_until="domcontentloaded")
            time.sleep(random.uniform(2.0, 4.0))

            # Check for CAPTCHA
            content = page.content()
            if "captcha" in content.lower() or "unusual traffic" in content.lower():
                print("[Google] CAPTCHA detected, skipping")
                browser.close()
                return results

            items = page.locator("div.g, div[data-sokoban-container]")
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

                    title_el = item.locator("h3").first
                    title = title_el.inner_text().strip() if title_el.count() > 0 else ""

                    snippet_el = item.locator("div[data-sncf], div.VwiC3b, span.aCOpRe, div[style*='-webkit-line-clamp']")
                    snippet = ""
                    if snippet_el.count() > 0:
                        snippet = snippet_el.first.inner_text().strip()

                    full_text = item.inner_text().strip()
                    results.append(RawResult(
                        linkedin_url=li_url, title=title,
                        snippet=snippet, full_text=full_text[:600], source="google",
                    ))
                except Exception:
                    continue
        except Exception as e:
            print(f"[Google] search error: {e}")
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
            time.sleep(random.uniform(2.0, 3.5))

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

def _fetch_linkedin_public_pages(urls: list[str]) -> dict[str, dict]:
    """Visit LinkedIn public profile pages without login using parallel tabs.
    Returns whatever LinkedIn shows to anonymous visitors: name, headline,
    current position, location, and sometimes truncated experience list.
    Zero risk -- this is the same page Google/Bing crawlers see.
    """
    data: dict[str, dict] = {}
    if not urls:
        return data

    BATCH_SIZE = 5

    with sync_playwright() as p:
        browser, context = _create_browser_context(p)

        for batch_start in range(0, len(urls), BATCH_SIZE):
            batch = urls[batch_start:batch_start + BATCH_SIZE]
            pages = []

            # Open all pages in batch simultaneously
            for url in batch:
                try:
                    page = context.new_page()
                    page.goto(url, wait_until="domcontentloaded", timeout=10000)
                    pages.append((url, page))
                except Exception as e:
                    print(f"[LinkedIn Public] nav failed for {url}: {e}")
                    continue

            time.sleep(random.uniform(1.5, 2.5))

            # Extract data from all loaded pages
            for url, page in pages:
                try:
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

                    try:
                        main_content = page.locator("main, .scaffold-layout__main, section.top-card-layout")
                        if main_content.count() > 0:
                            visible_text = main_content.first.inner_text(timeout=3000)
                            if visible_text and len(visible_text) > 20:
                                page_data["visible_text"] = visible_text[:1200]
                    except Exception:
                        pass

                    try:
                        body_text = page.locator("body").inner_text(timeout=3000)
                        if body_text and len(body_text) > 50:
                            page_data["body_text"] = body_text[:1500]
                    except Exception:
                        pass

                    if page_data:
                        data[_normalize_linkedin_url(url)] = page_data

                except Exception as e:
                    print(f"[LinkedIn Public] extract failed for {url}: {e}")

                try:
                    page.close()
                except Exception:
                    pass

        browser.close()
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
    if not m:
        m = re.search(r"(?:located?\s+in|based\s+in|from)\s+([A-Z][^.·\-|\n]{3,40})", text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def _extract_experience(text: str) -> str | None:
    m = re.search(r"Experience:?\s*(.+?)(?:\s*·\s*Education|$)", text, re.IGNORECASE)
    return m.group(1).strip()[:300] if m else None


def _extract_education(text: str) -> str | None:
    m = re.search(r"Education:?\s*(.+?)(?:\s*·\s*Location|\s*·\s*\d|$)", text, re.IGNORECASE)
    return m.group(1).strip()[:200] if m else None


def _parse_public_page(page_data: dict) -> dict:
    """Extract structured info from LinkedIn public page metadata."""
    info: dict = {}

    og_desc = page_data.get("og_description", "")
    meta_desc = page_data.get("meta_description", "")
    og_title = page_data.get("og_title", "")

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

    # Parse visible text for additional data
    visible = page_data.get("visible_text", "") or page_data.get("body_text", "")
    if visible and len(visible) > 50:
        info["visible_text"] = visible[:800]

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

    print(f"[MultiSearch] Launching parallel searches across 4 engines...")
    start_time = time.time()

    # Run all 4 search engines in parallel
    ddg_future = loop.run_in_executor(_executor, _search_duckduckgo, primary_query, max_results)
    bing_future = loop.run_in_executor(_executor, _search_bing, primary_query, max_results)
    google_future = loop.run_in_executor(_executor, _search_google, primary_query, max_results)
    brave_future = loop.run_in_executor(_executor, _search_brave, primary_query, max_results)

    # Wait for all to complete (or fail gracefully)
    ddg_results, bing_results, google_results, brave_results = await asyncio.gather(
        ddg_future, bing_future, google_future, brave_future,
        return_exceptions=True,
    )

    # Handle any exceptions from individual engines
    all_source_results: list[list[RawResult]] = []
    for name, result in [("DDG", ddg_results), ("Bing", bing_results),
                         ("Google", google_results), ("Brave", brave_results)]:
        if isinstance(result, Exception):
            print(f"[MultiSearch] {name} failed: {result}")
            all_source_results.append([])
        else:
            print(f"[MultiSearch] {name}: {len(result)} results")
            all_source_results.append(result)

    # If we have alternative terms and few results, run additional DDG searches
    total_raw = sum(len(r) for r in all_source_results)
    if total_raw < 10 and alternative_terms:
        print(f"[MultiSearch] Only {total_raw} results, trying alternative terms...")
        for alt in alternative_terms[:2]:
            alt_q = build_search_queries(alt, location, companies, seniority)[0]
            alt_results = await loop.run_in_executor(_executor, _search_duckduckgo, alt_q, 15)
            if not isinstance(alt_results, Exception):
                all_source_results.append(alt_results)
                print(f"[MultiSearch] Alt term '{alt[:30]}': {len(alt_results)} results")

    elapsed = time.time() - start_time
    print(f"[MultiSearch] All searches completed in {elapsed:.1f}s")

    # Collect all unique LinkedIn URLs for public page fetching
    all_urls: set[str] = set()
    for source_results in all_source_results:
        for r in source_results:
            all_urls.add(r.linkedin_url)

    # Fetch LinkedIn public pages (no login) for richer data
    print(f"[MultiSearch] Fetching {len(all_urls)} LinkedIn public pages (no login)...")
    public_start = time.time()
    url_list = list(all_urls)[:max_results + 10]
    public_pages = await loop.run_in_executor(_executor, _fetch_linkedin_public_pages, url_list)
    public_elapsed = time.time() - public_start
    print(f"[MultiSearch] Public pages fetched in {public_elapsed:.1f}s, got data for {len(public_pages)}")

    # Merge and deduplicate
    merged = _merge_results(all_source_results, public_pages)
    print(f"[MultiSearch] Merged to {len(merged)} unique profiles (from {sum(len(r) for r in all_source_results)} raw results)")

    return merged[:max_results], primary_query
