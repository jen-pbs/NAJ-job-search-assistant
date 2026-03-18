from pydantic import BaseModel


class Event(BaseModel):
    title: str
    url: str
    date: str | None = None
    location: str | None = None
    source: str | None = None
    description: str | None = None
    relevance_score: float | None = None
    relevance_reason: str | None = None


class EventSearchQuery(BaseModel):
    query: str
    location: str | None = None
    max_results: int = 15


class EventSearchResponse(BaseModel):
    query_used: str
    events: list[Event]
    total_found: int
