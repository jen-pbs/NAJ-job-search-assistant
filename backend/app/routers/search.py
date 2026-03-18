from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import SearchQuery, SearchResponse, SaveContactRequest
from app.services.web_search import search_linkedin_profiles
from app.services.profile_enricher import enrich_profiles
from app.services.ai_scorer import score_profiles
from app.services.query_interpreter import interpret_query
from app.services.notion_client import (
    save_contact_to_notion,
    get_database_schema,
    get_saved_contacts,
)

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/find-people", response_model=SearchResponse)
async def find_people(
    body: SearchQuery,
    settings: Settings = Depends(get_settings),
):
    """Find LinkedIn profiles matching the search criteria."""
    try:
        interpreted = body
        if settings.groq_api_key:
            try:
                interpreted = await interpret_query(body.query, settings.groq_api_key)
                interpreted.max_results = body.max_results
            except Exception as e:
                print(f"Query interpretation failed, using raw query: {e}")

        profiles, query_used = await search_linkedin_profiles(
            query=interpreted.query,
            location=interpreted.location or body.location,
            companies=interpreted.companies or body.companies,
            seniority=interpreted.seniority or body.seniority,
            alternative_terms=interpreted.alternative_terms,
            max_results=interpreted.max_results,
        )

        if profiles:
            # Enrich profiles by scraping public LinkedIn pages
            enrichments = None
            try:
                print(f"Enriching {min(len(profiles), 10)} profiles...")
                enrichments = await enrich_profiles(profiles, max_enrich=10)
                enriched_count = sum(1 for e in enrichments if e.get("enriched"))
                print(f"Successfully enriched {enriched_count}/{len(profiles)} profiles")
            except Exception as e:
                print(f"Profile enrichment failed, scoring with search data only: {e}")

            # AI scoring with enriched data
            if settings.groq_api_key:
                try:
                    profiles = await score_profiles(
                        profiles, body.query, settings.groq_api_key, enrichments
                    )
                except Exception as e:
                    print(f"AI scoring failed, returning unscored results: {e}")

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
            "description": "LinkedIn profile discovery via Playwright + Google",
            "steps": [
                "No setup needed! Search uses a headless browser automatically.",
                "Just start the backend and search.",
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
            "note": "The app works without this, but search results won't be scored or ranked",
        },
    }
