from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import SearchQuery, SearchResponse, SaveContactRequest
from app.services.google_search import search_linkedin_profiles
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
    if not settings.google_api_key or not settings.google_cse_id:
        raise HTTPException(
            status_code=400,
            detail="Google API key and Custom Search Engine ID are required. "
            "See /api/search/setup-guide for instructions.",
        )

    interpreted = body
    if settings.openai_api_key:
        interpreted = await interpret_query(body.query, settings.openai_api_key)
        interpreted.max_results = body.max_results

    profiles, query_used = await search_linkedin_profiles(
        query=interpreted.query,
        api_key=settings.google_api_key,
        cse_id=settings.google_cse_id,
        location=interpreted.location or body.location,
        companies=interpreted.companies or body.companies,
        seniority=interpreted.seniority or body.seniority,
        max_results=interpreted.max_results,
    )

    if settings.openai_api_key and profiles:
        profiles = await score_profiles(
            profiles, body.query, settings.openai_api_key
        )

    return SearchResponse(
        query_used=query_used,
        profiles=profiles,
        total_found=len(profiles),
    )


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
        raise HTTPException(
            status_code=400,
            detail="Notion API key is required.",
        )

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
        "google_custom_search": {
            "description": "Required for LinkedIn profile discovery via Google dorking",
            "steps": [
                "1. Go to https://console.cloud.google.com/",
                "2. Create a new project (or use existing)",
                "3. Enable the 'Custom Search API'",
                "4. Go to Credentials > Create Credentials > API Key",
                "5. Copy the API key to .env as GOOGLE_API_KEY",
                "6. Go to https://programmablesearchengine.google.com/",
                "7. Create a new search engine",
                "8. Set 'Search the entire web' to ON",
                "9. Copy the Search Engine ID to .env as GOOGLE_CSE_ID",
            ],
            "free_tier": "100 queries/day free",
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
        "openai": {
            "description": "Optional - enables AI query interpretation and relevance scoring",
            "steps": [
                "1. Go to https://platform.openai.com/api-keys",
                "2. Create a new API key",
                "3. Copy to .env as OPENAI_API_KEY",
            ],
            "note": "The app works without this, but search results won't be scored or ranked",
        },
    }
