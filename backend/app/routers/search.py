from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import SearchQuery, SearchResponse, SaveContactRequest
from app.services.web_search import search_linkedin_profiles
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

    interpreted = body
    if settings.openai_api_key:
        interpreted = await interpret_query(body.query, settings.openai_api_key)
        interpreted.max_results = body.max_results

    profiles, query_used = await search_linkedin_profiles(
        query=interpreted.query,
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
        "brave_search": {
            "description": "Required for LinkedIn profile discovery",
            "steps": [
                "1. Go to https://api-dashboard.search.brave.com/",
                "2. Sign up for a free account (no credit card needed)",
                "3. Subscribe to the Free plan (2000 queries/month)",
                "4. Copy your API key to .env as BRAVE_API_KEY",
            ],
            "free_tier": "2000 queries/month",
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
