"""Academic profile enrichment via Google Scholar and ORCID.

Searches Google Scholar for publications and ORCID for career data.
Both are zero risk -- public data, no authentication needed.
"""

import asyncio
import re
import time
import random
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

import httpx
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


# ---------------------------------------------------------------------------
# Google Scholar
# ---------------------------------------------------------------------------

def _search_google_scholar_sync(names: list[str]) -> dict[str, dict]:
    """Search Google Scholar for each person to find publications and research topics.
    Returns dict keyed by lowercase name."""
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

        for name in names:
            try:
                query = urllib.parse.quote(f'author:"{name}"')
                url = f"https://scholar.google.com/scholar?q={query}&hl=en"
                page.goto(url, wait_until="domcontentloaded")
                time.sleep(random.uniform(1.5, 2.5))

                # Check for CAPTCHA
                if "captcha" in page.content().lower() or "unusual traffic" in page.content().lower():
                    print("[Scholar] CAPTCHA detected, stopping")
                    break

                data: dict = {}

                # Look for a profile link (author page)
                profile_link = page.locator("a[href*='/citations?user=']").first
                if profile_link.count() > 0:
                    data["has_scholar_profile"] = True
                    profile_text = profile_link.inner_text().strip()
                    if profile_text:
                        data["scholar_name"] = profile_text

                # Extract article titles and snippets from search results
                articles = page.locator("div.gs_r.gs_or.gs_scl")
                article_count = min(articles.count(), 5)
                pubs = []
                for i in range(article_count):
                    try:
                        article = articles.nth(i)
                        title_el = article.locator("h3.gs_rt a, h3.gs_rt").first
                        title = title_el.inner_text().strip() if title_el.count() > 0 else ""
                        # Clean title
                        title = re.sub(r"^\[.*?\]\s*", "", title)

                        snippet_el = article.locator("div.gs_rs").first
                        snippet = snippet_el.inner_text().strip()[:200] if snippet_el.count() > 0 else ""

                        info_el = article.locator("div.gs_a").first
                        info = info_el.inner_text().strip() if info_el.count() > 0 else ""

                        if title:
                            pubs.append({
                                "title": title[:150],
                                "snippet": snippet,
                                "info": info[:150],
                            })
                    except Exception:
                        continue

                if pubs:
                    data["publications"] = pubs
                    data["publication_count"] = len(pubs)
                    # Extract research topics from titles
                    all_titles = " ".join(p["title"] for p in pubs)
                    data["research_summary"] = all_titles[:400]

                # Check for citation count on profile
                cite_el = page.locator("a[href*='/citations?user='] + span, .gs_nph")
                if cite_el.count() > 0:
                    cite_text = cite_el.first.inner_text().strip()
                    cite_match = re.search(r"(\d+)", cite_text.replace(",", ""))
                    if cite_match:
                        data["citation_count"] = int(cite_match.group(1))

                if data:
                    results[name.lower()] = data

            except Exception as e:
                print(f"[Scholar] Failed for {name}: {e}")
                continue

            time.sleep(random.uniform(1.0, 2.0))

        browser.close()

    return results


# ---------------------------------------------------------------------------
# ORCID (public API, no auth needed)
# ---------------------------------------------------------------------------

async def _search_orcid(names: list[str]) -> dict[str, dict]:
    """Search ORCID public API for career timeline data.
    Returns dict keyed by lowercase name."""
    results: dict[str, dict] = {}

    async with httpx.AsyncClient(timeout=10.0) as client:
        for name in names:
            try:
                # Search ORCID by name
                parts = name.strip().split()
                if len(parts) < 2:
                    continue

                given = parts[0]
                family = parts[-1]
                search_url = (
                    f"https://pub.orcid.org/v3.0/search/"
                    f"?q=given-names:{given}+AND+family-name:{family}"
                    f"&rows=3"
                )
                resp = await client.get(
                    search_url,
                    headers={"Accept": "application/json"},
                )

                if resp.status_code != 200:
                    continue

                search_data = resp.json()
                orcid_results = search_data.get("result", [])
                if not orcid_results:
                    continue

                # Get the first matching ORCID record
                orcid_id = orcid_results[0].get("orcid-identifier", {}).get("path")
                if not orcid_id:
                    continue

                # Fetch the full record
                record_url = f"https://pub.orcid.org/v3.0/{orcid_id}/record"
                record_resp = await client.get(
                    record_url,
                    headers={"Accept": "application/json"},
                )

                if record_resp.status_code != 200:
                    continue

                record = record_resp.json()
                data: dict = {"orcid_id": orcid_id}

                # Extract employment history
                employments = (
                    record.get("activities-summary", {})
                    .get("employments", {})
                    .get("affiliation-group", [])
                )
                jobs = []
                for group in employments[:5]:
                    summaries = group.get("summaries", [])
                    for s in summaries:
                        emp = s.get("employment-summary", {})
                        org = emp.get("organization", {})
                        role = emp.get("role-title", "")
                        org_name = org.get("name", "")
                        start = emp.get("start-date", {})
                        start_year = start.get("year", {}).get("value", "") if start else ""
                        end = emp.get("end-date", {})
                        end_year = end.get("year", {}).get("value", "Present") if end else "Present"

                        if org_name:
                            jobs.append({
                                "role": role,
                                "organization": org_name,
                                "start_year": start_year,
                                "end_year": end_year or "Present",
                            })

                if jobs:
                    data["employment_history"] = jobs

                # Extract education
                educations = (
                    record.get("activities-summary", {})
                    .get("educations", {})
                    .get("affiliation-group", [])
                )
                edu_list = []
                for group in educations[:5]:
                    summaries = group.get("summaries", [])
                    for s in summaries:
                        edu = s.get("education-summary", {})
                        org = edu.get("organization", {})
                        degree = edu.get("role-title", "")
                        org_name = org.get("name", "")
                        if org_name:
                            edu_list.append({
                                "degree": degree,
                                "institution": org_name,
                            })

                if edu_list:
                    data["education"] = edu_list

                # Extract works count
                works = (
                    record.get("activities-summary", {})
                    .get("works", {})
                    .get("group", [])
                )
                if works:
                    data["works_count"] = len(works)

                if len(data) > 1:  # more than just orcid_id
                    results[name.lower()] = data

            except Exception as e:
                print(f"[ORCID] Failed for {name}: {e}")
                continue

    return results


# ---------------------------------------------------------------------------
# Main enrichment function
# ---------------------------------------------------------------------------

async def enrich_with_academic_data(
    names: list[str],
    max_scholar: int = 15,
    max_orcid: int = 20,
) -> dict[str, dict]:
    """Enrich profiles with Google Scholar and ORCID data.

    Returns dict keyed by lowercase name with combined academic data.
    """
    if not names:
        return {}

    loop = asyncio.get_event_loop()

    # Run Scholar (Playwright) and ORCID (HTTP) in parallel
    print(f"[Academic] Enriching {len(names)} profiles (Scholar + ORCID)...")
    start = time.time()

    scholar_future = loop.run_in_executor(
        _executor, _search_google_scholar_sync, names[:max_scholar]
    )
    orcid_future = _search_orcid(names[:max_orcid])

    scholar_results, orcid_results = await asyncio.gather(
        scholar_future, orcid_future, return_exceptions=True
    )

    if isinstance(scholar_results, Exception):
        print(f"[Academic] Scholar failed: {scholar_results}")
        scholar_results = {}
    if isinstance(orcid_results, Exception):
        print(f"[Academic] ORCID failed: {orcid_results}")
        orcid_results = {}

    elapsed = time.time() - start
    print(f"[Academic] Done in {elapsed:.1f}s. Scholar: {len(scholar_results)}, ORCID: {len(orcid_results)}")

    # Merge results by name
    combined: dict[str, dict] = {}
    all_keys = set(list(scholar_results.keys()) + list(orcid_results.keys()))

    for key in all_keys:
        entry: dict = {}
        if key in scholar_results:
            entry["scholar"] = scholar_results[key]
        if key in orcid_results:
            entry["orcid"] = orcid_results[key]
        combined[key] = entry

    return combined
