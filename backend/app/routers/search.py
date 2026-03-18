from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import SearchQuery, SearchResponse, SaveContactRequest
from app.services.multi_search import search_linkedin_profiles_multi
from app.services.ai_scorer import score_merged_profiles
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
    """Find LinkedIn profiles using multi-source parallel search."""
    try:
        interpreted = body
        if settings.groq_api_key:
            try:
                interpreted = await interpret_query(body.query, settings.groq_api_key)
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
            if settings.groq_api_key:
                try:
                    profiles = await score_merged_profiles(
                        merged_profiles, body.query, settings.groq_api_key
                    )
                except Exception as e:
                    print(f"AI scoring failed, returning unscored results: {e}")
                    from app.services.ai_scorer import _merged_to_linkedin
                    profiles = [_merged_to_linkedin(m) for m in merged_profiles]
            else:
                from app.services.ai_scorer import _merged_to_linkedin
                profiles = [_merged_to_linkedin(m) for m in merged_profiles]

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
