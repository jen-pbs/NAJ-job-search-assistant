from pydantic import BaseModel
from enum import Enum


class ContactStatus(str, Enum):
    DISCOVERED = "Discovered"
    TO_CONTACT = "To Contact"
    CONTACTED = "Contacted"
    SCHEDULED = "Scheduled"
    COMPLETED = "Completed"
    NOT_RELEVANT = "Not Relevant"


class SearchQuery(BaseModel):
    query: str
    location: str | None = None
    companies: list[str] | None = None
    seniority: str | None = None
    max_results: int = 20


class LinkedInProfile(BaseModel):
    name: str
    headline: str | None = None
    location: str | None = None
    linkedin_url: str
    snippet: str | None = None
    relevance_score: float | None = None
    relevance_reason: str | None = None


class SearchResponse(BaseModel):
    query_used: str
    profiles: list[LinkedInProfile]
    total_found: int


class SaveContactRequest(BaseModel):
    name: str
    headline: str | None = None
    location: str | None = None
    linkedin_url: str
    relevance_score: float | None = None
    relevance_reason: str | None = None
    status: ContactStatus = ContactStatus.DISCOVERED
    notes: str | None = None
    domain: str | None = None
