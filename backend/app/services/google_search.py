import httpx
import re
from urllib.parse import quote_plus

from app.models.schemas import LinkedInProfile


GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"


def build_dork_queries(
    query: str,
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
) -> list[str]:
    """Build Google dork queries from search parameters."""
    base = 'site:linkedin.com/in'
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


async def search_google_cse(
    query: str,
    api_key: str,
    cse_id: str,
    num_results: int = 10,
    start: int = 1,
) -> list[dict]:
    """Search using Google Custom Search Engine API."""
    params = {
        "key": api_key,
        "cx": cse_id,
        "q": query,
        "num": min(num_results, 10),
        "start": start,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(GOOGLE_CSE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    return data.get("items", [])


def parse_linkedin_result(item: dict) -> LinkedInProfile | None:
    """Parse a Google search result into a LinkedInProfile."""
    link = item.get("link", "")
    if "linkedin.com/in/" not in link:
        return None

    title = item.get("title", "")
    snippet = item.get("snippet", "")

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


async def search_linkedin_profiles(
    query: str,
    api_key: str,
    cse_id: str,
    location: str | None = None,
    companies: list[str] | None = None,
    seniority: str | None = None,
    max_results: int = 20,
) -> tuple[list[LinkedInProfile], str]:
    """Run the full search pipeline: build dorks, query Google, parse results."""
    dork_queries = build_dork_queries(query, location, companies, seniority)

    profiles: list[LinkedInProfile] = []
    seen_urls: set[str] = set()

    for dork in dork_queries:
        if len(profiles) >= max_results:
            break

        remaining = max_results - len(profiles)
        pages_needed = (remaining + 9) // 10

        for page in range(pages_needed):
            start = page * 10 + 1
            try:
                items = await search_google_cse(
                    dork, api_key, cse_id, num_results=10, start=start
                )
            except httpx.HTTPStatusError:
                break

            for item in items:
                profile = parse_linkedin_result(item)
                if profile and profile.linkedin_url not in seen_urls:
                    seen_urls.add(profile.linkedin_url)
                    profiles.append(profile)

            if len(items) < 10:
                break

    return profiles[:max_results], dork_queries[0]
