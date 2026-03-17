import asyncio
import random
import re

from playwright.async_api import async_playwright

from app.models.schemas import LinkedInProfile


def build_search_queries(
    query: str,
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
) -> list[str]:
    """Build search queries optimized for LinkedIn profile discovery."""
    base = "site:linkedin.com/in"
    parts = [base, f'"{query}"']

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
            chunk_parts = [base, f'"{query}"']
            if location:
                chunk_parts.append(f'"{location}"')
            chunk_clause = " OR ".join(f'"{c}"' for c in chunk)
            chunk_parts.append(f"({chunk_clause})")
            queries.append(" ".join(chunk_parts))

    return queries


async def _search_google_playwright(query: str, max_results: int = 20) -> list[dict]:
    """Search Google using a headless browser. No API key needed."""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            viewport={"width": 1280, "height": 800},
        )
        # Accept cookies automatically
        context.set_default_timeout(15000)
        page = await context.new_page()

        try:
            await page.goto("https://www.google.com/search?q=" + query.replace(" ", "+") + f"&num={min(max_results, 20)}&hl=en", wait_until="domcontentloaded")
            await asyncio.sleep(random.uniform(1.5, 3.0))

            # Handle cookie consent if it appears
            try:
                accept_btn = page.locator("button:has-text('Accept all'), button:has-text('Accept'), button:has-text('I agree')")
                if await accept_btn.count() > 0:
                    await accept_btn.first.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # Check for CAPTCHA
            content = await page.content()
            if "sorry" in content.lower() and "unusual traffic" in content.lower():
                print("Google CAPTCHA detected. Try again later or reduce search frequency.")
                await browser.close()
                return []

            # Extract search results
            result_elements = page.locator("div.g")
            count = await result_elements.count()

            for i in range(min(count, max_results)):
                try:
                    el = result_elements.nth(i)

                    link_el = el.locator("a").first
                    href = await link_el.get_attribute("href") or ""

                    title_el = el.locator("h3").first
                    title = await title_el.inner_text() if await title_el.count() > 0 else ""

                    # Get snippet from various possible selectors
                    snippet = ""
                    for sel in ["div[data-sncf]", "div.VwiC3b", "span.aCOpRe", "div[style='-webkit-line-clamp:2']"]:
                        snippet_el = el.locator(sel).first
                        if await snippet_el.count() > 0:
                            snippet = await snippet_el.inner_text()
                            break

                    if href:
                        results.append({
                            "link": href,
                            "title": title,
                            "snippet": snippet,
                        })
                except Exception:
                    continue

            # If div.g didn't work, try broader extraction
            if not results:
                all_links = page.locator("a[href*='linkedin.com/in/']")
                link_count = await all_links.count()
                for i in range(min(link_count, max_results)):
                    try:
                        el = all_links.nth(i)
                        href = await el.get_attribute("href") or ""
                        text = await el.inner_text()
                        if "linkedin.com/in/" in href:
                            results.append({
                                "link": href,
                                "title": text,
                                "snippet": "",
                            })
                    except Exception:
                        continue

        except Exception as e:
            print(f"Playwright search error: {e}")
        finally:
            await browser.close()

    return results


def parse_linkedin_result(item: dict) -> LinkedInProfile | None:
    """Parse a search result into a LinkedInProfile."""
    link = item.get("link", "")
    if "linkedin.com/in/" not in link:
        return None

    title = item.get("title", "")
    snippet = item.get("snippet", "")

    if not title:
        return _parse_url_into_profile(link)

    name = title.split(" - ")[0].strip() if " - " in title else title.split("|")[0].strip()
    name = re.sub(r"\s*\|.*$", "", name)
    name = re.sub(r"\s*–.*$", "", name)

    headline = None
    if " - " in title:
        parts = title.split(" - ")
        if len(parts) >= 2:
            headline = parts[1].strip()
            headline = re.sub(r"\s*\|.*$", "", headline)
            headline = re.sub(r"\s*–.*$", "", headline)

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


def _parse_url_into_profile(url: str) -> LinkedInProfile | None:
    """Extract name from a LinkedIn profile URL as fallback."""
    if "linkedin.com/in/" not in url:
        return None

    clean_url = re.sub(r"\?.*$", "", url)
    slug = clean_url.rstrip("/").split("/")[-1]
    name = slug.replace("-", " ").title()
    name = re.sub(r"\s+\d+$", "", name)

    return LinkedInProfile(
        name=name,
        headline=None,
        location=None,
        linkedin_url=clean_url,
        snippet=None,
    )


async def search_linkedin_profiles(
    query: str,
    api_key: str = "",
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
    max_results: int = 20,
) -> tuple[list[LinkedInProfile], str]:
    """Search for LinkedIn profiles using Playwright + Google. No API key needed."""
    search_queries = build_search_queries(query, location, companies, seniority)

    profiles: list[LinkedInProfile] = []
    seen_urls: set[str] = set()

    for sq in search_queries:
        if len(profiles) >= max_results:
            break

        remaining = max_results - len(profiles)
        items = await _search_google_playwright(sq, max_results=remaining)

        for item in items:
            profile = parse_linkedin_result(item)
            if profile and profile.linkedin_url not in seen_urls:
                seen_urls.add(profile.linkedin_url)
                profiles.append(profile)

        # Random delay between queries to be polite
        if len(search_queries) > 1:
            await asyncio.sleep(random.uniform(2.0, 5.0))

    return profiles[:max_results], search_queries[0]
