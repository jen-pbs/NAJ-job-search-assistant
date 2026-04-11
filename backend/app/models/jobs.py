from pydantic import BaseModel


class Job(BaseModel):
    title: str
    company: str | None = None
    url: str
    location: str | None = None
    salary: str | None = None
    date_posted: str | None = None
    source: str | None = None
    description: str | None = None
    is_remote: bool | None = None


class JobSearchQuery(BaseModel):
    query: str
    location: str | None = None
    max_results: int = 25
    user_context: str | None = None
    ai_model: str | None = None
    ai_provider: str | None = None
    ai_api_key: str | None = None
    ai_base_url: str | None = None


class JobSearchResponse(BaseModel):
    query_used: str
    jobs: list[Job]
    total_found: int
