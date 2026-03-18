import asyncio
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor

from playwright.sync_api import sync_playwright

from app.models.schemas import LinkedInProfile

_executor = ThreadPoolExecutor(max_workers=1)

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime: {}};
"""


def _enrich_via_duckduckgo(profiles: list[dict]) -> list[dict]:
    """Enrich profiles by searching DuckDuckGo for each person's name + LinkedIn.
    DDG snippets contain role, company, experience summary that LinkedIn blocks."""
    enrichments = []

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
        context.set_default_timeout(10000)
        context.add_init_script(STEALTH_JS)

        for profile_data in profiles:
            name = profile_data["name"]
            url = profile_data["url"]
            slug = url.rstrip("/").split("/")[-1]

            data: dict = {"url": url, "enriched": False}

            try:
                page = context.new_page()

                query = f'"{name}" site:linkedin.com/in'
                page.goto(
                    f"https://duckduckgo.com/?q={query.replace(' ', '+')}",
                    wait_until="domcontentloaded",
                )
                time.sleep(random.uniform(1.5, 2.5))

                # Find the article that matches this person's LinkedIn URL
                articles = page.locator("article")
                count = articles.count()

                best_text = ""
                name_parts = [p.lower() for p in name.split() if len(p) > 2]
                for i in range(min(count, 5)):
                    try:
                        article = articles.nth(i)
                        text = article.inner_text()
                        text_lower = text.lower()
                        # Match if the article mentions the person's name parts
                        matches = sum(1 for part in name_parts if part in text_lower)
                        if matches >= 2 or slug.replace("-", " ") in text_lower:
                            if len(text) > len(best_text):
                                best_text = text
                    except Exception:
                        continue

                if best_text and len(best_text) > 50:
                    parsed = _parse_ddg_snippet(best_text, name)
                    data.update(parsed)
                    data["enriched"] = True

                page.close()

            except Exception as e:
                print(f"Enrichment failed for {name}: {e}")

            enrichments.append(data)

            if len(profiles) > 1:
                time.sleep(random.uniform(0.5, 1.5))

        browser.close()

    return enrichments


def _parse_ddg_snippet(text: str, name: str) -> dict:
    """Parse a DuckDuckGo article snippet into structured profile data."""
    data: dict = {}
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    # Find the title line (usually "Name - Headline | LinkedIn" or similar)
    for line in lines:
        if "linkedin" in line.lower() and (" - " in line or "|" in line):
            parts = re.split(r'\s*[-|]\s*', line)
            parts = [p.strip() for p in parts if p.strip() and "linkedin" not in p.lower()]
            if len(parts) >= 2:
                data["headline"] = parts[1] if parts[0].lower() in name.lower() else parts[0]
            break

    # The remaining text after the title is usually the description
    # Find the longest line that isn't the title or URL
    description_parts = []
    for line in lines:
        if (
            "linkedin" not in line.lower()
            and "http" not in line.lower()
            and len(line) > 30
            and line != data.get("headline", "")
        ):
            description_parts.append(line)

    if description_parts:
        full_desc = " ".join(description_parts)

        # Extract experience info
        exp_match = re.search(r"Experience:\s*(.+?)(?:\s*·|\s*Education:|$)", full_desc)
        if exp_match:
            data["experience_text"] = exp_match.group(1).strip()

        # Extract education info
        edu_match = re.search(r"Education:\s*(.+?)(?:\s*·|\s*Location:|$)", full_desc)
        if edu_match:
            data["education_text"] = edu_match.group(1).strip()

        # Extract location
        loc_match = re.search(r"Location:\s*(.+?)(?:\s*·|\s*\d+|$)", full_desc)
        if loc_match:
            data["location"] = loc_match.group(1).strip()

        # Store the full description for AI to parse
        data["description"] = full_desc[:600]

    return data


async def enrich_profiles(
    profiles: list[LinkedInProfile],
    max_enrich: int = 10,
) -> list[dict]:
    """Enrich profiles by searching DuckDuckGo for additional details."""
    profile_data = [
        {"name": p.name, "url": p.linkedin_url}
        for p in profiles[:max_enrich]
    ]

    loop = asyncio.get_event_loop()
    enrichments = await loop.run_in_executor(_executor, _enrich_via_duckduckgo, profile_data)

    while len(enrichments) < len(profiles):
        enrichments.append({"url": profiles[len(enrichments)].linkedin_url, "enriched": False})

    return enrichments
