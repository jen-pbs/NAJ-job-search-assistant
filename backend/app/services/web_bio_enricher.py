"""Open web enrichment for professional profiles.

Searches DuckDuckGo for conference speaker bios, press releases,
Crunchbase profiles, company team pages, and industry association
mentions. Targets non-academic professionals whose career data
lives outside LinkedIn and Google Scholar.

Zero risk -- all public web data.
"""

import asyncio
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright

_executor = ThreadPoolExecutor(max_workers=2)

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime: {}};
"""

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def _build_enrichment_queries(name: str, company: str | None, headline: str | None) -> list[str]:
    """Build targeted queries to find professional bios and career data.
    Uses simple keyword queries (DDG handles OR/quoted badly in complex combos).
    """
    queries = []

    # Professional bio with company context
    if company:
        # Clean company name (remove "Location:" artifacts etc.)
        clean_company = company.split("·")[0].split("Location")[0].strip()[:50]
        queries.append(f"{name} {clean_company} bio speaker")
    else:
        queries.append(f"{name} bio speaker healthcare pharma")

    # Career trajectory and appointments
    if company:
        clean_company = company.split("·")[0].split("Location")[0].strip()[:50]
        queries.append(f"{name} {clean_company} career previously appointed")
    else:
        queries.append(f"{name} career background appointed promoted")

    # Crunchbase + industry associations
    queries.append(f"{name} crunchbase ISPOR AMCP conference")

    return queries


def _extract_bio_snippets(page_text: str, name: str) -> dict:
    """Extract useful biographical information from a web page."""
    data: dict = {}
    name_parts = [p.lower() for p in name.split() if len(p) > 2]
    text_lower = page_text.lower()

    # Check if page actually mentions this person
    match_count = sum(1 for part in name_parts if part in text_lower)
    if match_count < 2:
        return data

    lines = [l.strip() for l in page_text.split("\n") if l.strip()]

    # Find the most informative paragraph about this person
    best_bio = ""
    best_score = 0
    bio_keywords = [
        "experience", "years", "previously", "prior", "career",
        "responsible", "oversees", "leads", "manages", "specializ",
        "expertise", "background", "joined", "served", "worked",
        "degree", "university", "mba", "phd", "pharmd",
        "vice president", "director", "senior", "head of",
        "board", "committee", "fellow",
    ]

    for i, line in enumerate(lines):
        if len(line) < 50 or len(line) > 800:
            continue
        line_lower = line.lower()

        # Skip navigation, menus, cookie notices
        if any(skip in line_lower for skip in ["cookie", "privacy", "subscribe", "sign up", "log in", "©"]):
            continue

        # Score this line for biographical content
        score = 0
        score += sum(1 for part in name_parts if part in line_lower) * 3
        score += sum(1 for kw in bio_keywords if kw in line_lower)
        # Bonus for longer, structured text
        if len(line) > 100:
            score += 2
        if len(line) > 200:
            score += 2

        if score > best_score:
            best_score = score
            # Also grab the next line for continuation
            bio_text = line
            if i + 1 < len(lines) and len(lines[i + 1]) > 30:
                next_line = lines[i + 1]
                if not any(skip in next_line.lower() for skip in ["cookie", "privacy", "subscribe"]):
                    bio_text += " " + next_line
            best_bio = bio_text[:600]

    if best_bio and best_score >= 4:
        data["bio_text"] = best_bio

    # Extract specific career mentions
    career_mentions = []
    for line in lines:
        line_lower = line.lower()
        if len(line) < 20 or len(line) > 500:
            continue
        has_name = sum(1 for part in name_parts if part in line_lower) >= 2

        if has_name:
            # Look for career transition phrases
            if any(phrase in line_lower for phrase in [
                "appointed", "promoted", "named", "joins", "joined",
                "previously", "prior to", "before joining", "formerly",
                "served as", "was the", "held the position",
            ]):
                career_mentions.append(line[:300])

    if career_mentions:
        data["career_mentions"] = career_mentions[:3]

    # Extract company associations
    companies_found = set()
    company_patterns = [
        r"(?:at|with|for|from|joined|left)\s+([A-Z][A-Za-z&\s]{2,25})",
    ]
    skip_words = {"the", "their", "this", "that", "with", "and", "for", "from", "has", "was"}
    for line in lines:
        if sum(1 for part in name_parts if part in line.lower()) < 1:
            continue
        for pattern in company_patterns:
            matches = re.findall(pattern, line)
            for m in matches:
                m = m.strip().rstrip(".,;:")
                # Skip if it's a person's name or generic word
                if (len(m) < 4 or m.lower() in skip_words
                    or any(part in m.lower() for part in name_parts)):
                    continue
                companies_found.add(m)

    if companies_found:
        data["companies_mentioned"] = list(companies_found)[:5]

    return data


def _search_web_bios_sync(profiles: list[dict]) -> dict[str, dict]:
    """Search DuckDuckGo for professional bios and career data.
    
    profiles: list of dicts with 'name', 'company', 'headline' keys.
    Returns dict keyed by lowercase name.
    """
    results: dict[str, dict] = {}

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True, channel="chrome",
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
            )
        except Exception:
            browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            user_agent=USER_AGENT, locale="en-US",
            viewport={"width": 1366, "height": 768},
        )
        context.set_default_timeout(10000)
        context.add_init_script(STEALTH_JS)
        page = context.new_page()

        for profile in profiles:
            name = profile["name"]
            company = profile.get("company")
            headline = profile.get("headline")
            name_key = name.lower()

            queries = _build_enrichment_queries(name, company, headline)
            profile_data: dict = {"sources_checked": []}
            all_snippets: list[str] = []
            bio_data: dict = {}

            for query in queries[:3]:  # Limit to 3 queries per person
                try:
                    url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
                    page.goto(url, wait_until="domcontentloaded")
                    time.sleep(random.uniform(1.5, 2.5))

                    articles = page.locator("article")
                    count = min(articles.count(), 5)

                    for i in range(count):
                        try:
                            article = articles.nth(i)
                            text = article.inner_text().strip()

                            # Skip LinkedIn results (we already have those)
                            if "linkedin.com" in text.lower():
                                continue

                            # Check if this result is about our person
                            text_lower = text.lower()
                            name_parts = [pt.lower() for pt in name.split() if len(pt) > 1]
                            name_match = sum(1 for pt in name_parts if pt in text_lower)
                            # Need at least first+last name to match
                            min_match = min(2, len(name_parts))
                            if name_match < min_match:
                                continue

                            # Extract the href to identify the source
                            link_el = article.locator("a[href]").first
                            href = ""
                            if link_el.count() > 0:
                                href = (link_el.get_attribute("href") or "").lower()

                            # Categorize the source
                            source_type = "web"
                            if "crunchbase.com" in href:
                                source_type = "crunchbase"
                            elif any(s in href for s in ["ispor.org", "amcp.org", "diaglobal.org", "bio.org"]):
                                source_type = "industry_association"
                            elif any(s in href for s in ["prnewswire", "businesswire", "globenewswire", "pr.com"]):
                                source_type = "press_release"
                            elif any(s in text_lower for s in ["speaker", "panelist", "presenter", "keynote"]):
                                source_type = "conference"

                            if source_type not in profile_data["sources_checked"]:
                                profile_data["sources_checked"].append(source_type)

                            # Get snippet lines
                            lines = [l.strip() for l in text.split("\n") if l.strip()]
                            for line in lines:
                                if len(line) > 50 and "linkedin" not in line.lower() and "http" not in line.lower():
                                    all_snippets.append(line[:300])
                                    break

                            # Try to extract bio from full text
                            extracted = _extract_bio_snippets(text, name)
                            if extracted:
                                # Merge into bio_data, preferring longer texts
                                if extracted.get("bio_text"):
                                    if not bio_data.get("bio_text") or len(extracted["bio_text"]) > len(bio_data.get("bio_text", "")):
                                        bio_data["bio_text"] = extracted["bio_text"]
                                if extracted.get("career_mentions"):
                                    existing = bio_data.get("career_mentions", [])
                                    for mention in extracted["career_mentions"]:
                                        if mention not in existing:
                                            existing.append(mention)
                                    bio_data["career_mentions"] = existing[:5]
                                if extracted.get("companies_mentioned"):
                                    existing = set(bio_data.get("companies_mentioned", []))
                                    existing.update(extracted["companies_mentioned"])
                                    bio_data["companies_mentioned"] = list(existing)[:8]

                        except Exception:
                            continue

                except Exception as e:
                    print(f"[WebBio] Query failed for {name}: {e}")
                    continue

                time.sleep(random.uniform(0.8, 1.5))

            # Combine everything
            if bio_data:
                profile_data.update(bio_data)
            if all_snippets:
                # Deduplicate and keep most informative
                unique_snippets = []
                for s in all_snippets:
                    if not any(s[:50] in existing for existing in unique_snippets):
                        unique_snippets.append(s)
                profile_data["web_snippets"] = unique_snippets[:5]

            if len(profile_data) > 1:  # More than just sources_checked
                results[name_key] = profile_data

        browser.close()

    return results


async def enrich_with_web_bios(
    profiles: list[dict],
    max_profiles: int = 10,
) -> dict[str, dict]:
    """Enrich profiles with open web data (bios, press releases, etc.).

    profiles: list of dicts with 'name', 'company', 'headline' keys.
    Returns dict keyed by lowercase name.
    """
    if not profiles:
        return {}

    print(f"[WebBio] Enriching {min(len(profiles), max_profiles)} profiles from open web...")
    start = time.time()

    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(
        _executor, _search_web_bios_sync, profiles[:max_profiles]
    )

    if isinstance(results, Exception):
        print(f"[WebBio] Failed: {results}")
        return {}

    elapsed = time.time() - start
    print(f"[WebBio] Done in {elapsed:.1f}s. Found data for {len(results)}/{len(profiles)} profiles")

    return results
