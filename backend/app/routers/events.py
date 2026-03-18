from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.events import EventSearchQuery, EventSearchResponse
from app.services.event_search import search_events

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/search", response_model=EventSearchResponse)
async def find_events(
    body: EventSearchQuery,
    settings: Settings = Depends(get_settings),
):
    """Search for networking events, conferences, and meetups."""
    try:
        events, query_used = await search_events(
            query=body.query,
            location=body.location,
            max_results=body.max_results,
        )

        return EventSearchResponse(
            query_used=query_used,
            events=events,
            total_found=len(events),
        )
    except Exception as e:
        print(f"Event search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
