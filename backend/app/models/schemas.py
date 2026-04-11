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
    alternative_terms: list[str] | None = None
    max_results: int = 20
    user_context: str | None = None
    ai_model: str | None = None
    ai_provider: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None


class LinkedInProfile(BaseModel):
    name: str
    headline: str | None = None
    location: str | None = None
    linkedin_url: str
    snippet: str | None = None
    relevance_score: float | None = None
    relevance_reason: str | None = None
    company: str | None = None
    role_title: str | None = None
    field: str | None = None
    company_type: str | None = None
    saved_in_notion: bool = False
    notion_page_url: str | None = None


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
    company: str | None = None
    role_title: str | None = None
    status: ContactStatus = ContactStatus.DISCOVERED
    notes: str | None = None
    domain: str | None = None
    field: str | None = None
    company_type: str | None = None
