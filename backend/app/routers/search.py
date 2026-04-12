from fastapi import APIRouter, Depends, HTTPException
from urllib.parse import urlsplit, urlunsplit

from app.config import Settings, get_settings
from app.models.schemas import SearchQuery, SearchResponse, SaveContactRequest
from app.services.multi_search import search_linkedin_profiles_multi
from app.services.academic_enricher import enrich_with_academic_data
from app.services.web_bio_enricher import enrich_with_web_bios
from app.services.ai_scorer import score_merged_profiles
from app.services.query_interpreter import interpret_query
from app.services.ai_provider import resolve_ai_connection
from app.services.notion_client import (
    save_contact_to_notion,
    get_database_schema,
    get_saved_contacts,
)

router = APIRouter(prefix="/api/search", tags=["search"])


def _normalize_linkedin_url(url: str | None) -> str:
    if not url:
        return ""
    cleaned = url.strip()
    if not cleaned:
        return ""
    try:
        parsed = urlsplit(cleaned)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = (parsed.path or "").rstrip("/")
        return urlunsplit((parsed.scheme.lower(), netloc, path, "", ""))
    except Exception:
        return cleaned.rstrip("/").lower()


def _build_saved_lookup(saved_contacts: list[dict]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for contact in saved_contacts:
        linkedin_url = contact.get("LinkedIn") or contact.get("linkedin_url")
        normalized = _normalize_linkedin_url(linkedin_url)
        if normalized:
            lookup[normalized] = contact.get("url", "")
    return lookup


@router.post("/find-people", response_model=SearchResponse)
async def find_people(
    body: SearchQuery,
    settings: Settings = Depends(get_settings),
):
    """Find LinkedIn profiles using multi-source parallel search."""
    try:
        ai_connection = None
        ai_config_explicit = any(
            [
                (body.ai_provider or "").strip(),
                (body.ai_api_key or "").strip(),
                (body.ai_base_url or "").strip(),
            ]
        )
        try:
            ai_connection = resolve_ai_connection(
                settings=settings,
                ai_provider=body.ai_provider,
                ai_api_key=body.ai_api_key,
                ai_base_url=body.ai_base_url,
            )
            print(f"[Search] AI connection resolved: provider={ai_connection.get('provider')}, has_key={bool(ai_connection.get('api_key'))}")
        except ValueError as e:
            print(f"[Search] AI connection failed: {e}")
            if ai_config_explicit:
                raise HTTPException(status_code=400, detail=f"AI settings error: {e}")

        interpreted = body
        if ai_connection:
            try:
                interpreted = await interpret_query(
                    body.query,
                    ai_connection["api_key"],
                    body.user_context,
                    body.ai_model or settings.ai_model,
                    ai_connection["base_url"],
                )
                interpreted.max_results = body.max_results
            except Exception as e:
                print(f"Query interpretation failed, using raw query: {e}")

        merged_profiles, query_used = await search_linkedin_profiles_multi(
            query=interpreted.query,
            location=interpreted.location or body.location,
            companies=interpreted.companies or body.companies,
            seniority=interpreted.seniority or body.seniority,
            alternative_terms=interpreted.alternative_terms,
            max_results=interpreted.max_results,
        )

        profiles = []
        if merged_profiles:
            # Enrich with all sources in parallel:
            # - Academic: Google Scholar + ORCID (researchers)
            # - Web bios: conference bios, press releases, Crunchbase (industry)
            import asyncio as _aio
            try:
                names = [p.name for p in merged_profiles if p.name]
                web_profiles = [
                    {"name": p.name, "company": p.experience_text, "headline": p.headline}
                    for p in merged_profiles if p.name
                ]

                academic_task = enrich_with_academic_data(names)
                web_bio_task = enrich_with_web_bios(web_profiles)

                academic_data, web_bio_data = await _aio.gather(
                    academic_task, web_bio_task, return_exceptions=True,
                )

                if isinstance(academic_data, Exception):
                    print(f"Academic enrichment failed: {academic_data}")
                    academic_data = {}
                if isinstance(web_bio_data, Exception):
                    print(f"Web bio enrichment failed: {web_bio_data}")
                    web_bio_data = {}

                for mp in merged_profiles:
                    key = mp.name.lower()
                    if key in academic_data:
                        ad = academic_data[key]
                        if "scholar" in ad:
                            mp.scholar_data = ad["scholar"]
                            if "scholar" not in mp.sources:
                                mp.sources.append("scholar")
                        if "orcid" in ad:
                            mp.orcid_data = ad["orcid"]
                            if "orcid" not in mp.sources:
                                mp.sources.append("orcid")
                    if key in web_bio_data:
                        mp.web_bio_data = web_bio_data[key]
                        for src in web_bio_data[key].get("sources_checked", []):
                            if src not in mp.sources and src != "web":
                                mp.sources.append(src)
                        if "web_bio" not in mp.sources:
                            mp.sources.append("web_bio")

                academic_count = sum(1 for mp in merged_profiles if mp.scholar_data or mp.orcid_data)
                web_count = sum(1 for mp in merged_profiles if mp.web_bio_data)
                print(f"Enrichment: {academic_count} academic, {web_count} web bio out of {len(merged_profiles)} profiles")
            except Exception as e:
                print(f"Enrichment failed (continuing without): {e}")

            if ai_connection:
                print(f"[Search] Starting AI scoring for {len(merged_profiles)} profiles...")
                try:
                    profiles = await score_merged_profiles(
                        merged_profiles,
                        body.query,
                        ai_connection["api_key"],
                        body.user_context,
                        body.ai_model or settings.ai_model,
                        ai_connection["base_url"],
                    )
                    scored_count = sum(1 for p in profiles if p.relevance_score is not None)
                    print(f"[Search] AI scoring complete: {scored_count}/{len(profiles)} scored")
                except Exception as e:
                    print(f"[Search] AI scoring FAILED: {e}")
                    from app.services.ai_scorer import _merged_to_linkedin
                    profiles = [_merged_to_linkedin(m) for m in merged_profiles]
            else:
                from app.services.ai_scorer import _merged_to_linkedin
                profiles = [_merged_to_linkedin(m) for m in merged_profiles]

        if profiles and settings.notion_api_key:
            try:
                saved_contacts = await get_saved_contacts(
                    settings.notion_api_key, settings.notion_database_id
                )
                saved_lookup = _build_saved_lookup(saved_contacts)
                for profile in profiles:
                    normalized = _normalize_linkedin_url(profile.linkedin_url)
                    if normalized and normalized in saved_lookup:
                        profile.saved_in_notion = True
                        profile.notion_page_url = saved_lookup[normalized] or None
            except Exception as e:
                print(f"Saved-contact lookup failed (continuing): {e}")

        return SearchResponse(
            query_used=query_used,
            profiles=profiles,
            total_found=len(profiles),
        )
    except Exception as e:
        print(f"Search endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-contact")
async def save_contact(
    body: SaveContactRequest,
    settings: Settings = Depends(get_settings),
):
    """Save a discovered contact to the Notion database."""
    if not settings.notion_api_key:
        raise HTTPException(
            status_code=400,
            detail="Notion API key is required. Set NOTION_API_KEY in .env",
        )

    try:
        result = await save_contact_to_notion(
            api_key=settings.notion_api_key,
            database_id=settings.notion_database_id,
            contact=body,
        )
        return {"status": "saved", "notion_page": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save to Notion: {e}")


@router.get("/notion-schema")
async def notion_schema(settings: Settings = Depends(get_settings)):
    """Get the schema of the connected Notion database."""
    if not settings.notion_api_key:
        raise HTTPException(status_code=400, detail="Notion API key is required.")

    try:
        schema = await get_database_schema(
            settings.notion_api_key, settings.notion_database_id
        )
        return schema
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to read Notion database: {e}"
        )


@router.get("/saved-contacts")
async def list_saved_contacts(settings: Settings = Depends(get_settings)):
    """List contacts already saved in Notion."""
    if not settings.notion_api_key:
        raise HTTPException(status_code=400, detail="Notion API key is required.")

    try:
        contacts = await get_saved_contacts(
            settings.notion_api_key, settings.notion_database_id
        )
        return {"contacts": contacts, "total": len(contacts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch contacts: {e}")


@router.get("/setup-guide")
async def setup_guide():
    """Return setup instructions for required API keys."""
    return {
        "search": {
            "description": "Multi-source LinkedIn profile discovery (DDG + Bing + Google + Brave + LinkedIn public pages)",
            "steps": [
                "No setup needed! Search uses headless browsers across 4 search engines automatically.",
                "LinkedIn public profiles are fetched anonymously for richer data.",
            ],
            "free_tier": "Unlimited (no API key required)",
        },
        "notion": {
            "description": "Required for saving contacts to your existing database",
            "steps": [
                "1. Go to https://www.notion.so/my-integrations",
                "2. Click 'New integration'",
                "3. Name it 'Job Search Assistant'",
                "4. Copy the Internal Integration Secret to .env as NOTION_API_KEY",
                "5. In Notion, open your Informational Interviews page",
                "6. Click '...' menu > 'Connections' > Add your integration",
            ],
        },
        "groq": {
            "description": "Optional (free) - enables AI query interpretation and relevance scoring",
            "steps": [
                "1. Go to https://console.groq.com/",
                "2. Sign up (free, no credit card)",
                "3. Go to API Keys > Create API Key",
                "4. Copy to .env as GROQ_API_KEY",
            ],
            "free_tier": "30 req/min, 1000 req/day, free forever",
        },
    }
