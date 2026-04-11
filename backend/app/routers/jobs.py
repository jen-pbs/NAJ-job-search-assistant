from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.jobs import JobSearchQuery, JobSearchResponse
from app.services.job_search import search_jobs, interpret_job_query
from app.services.ai_provider import resolve_ai_connection

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/search", response_model=JobSearchResponse)
async def find_jobs(
    body: JobSearchQuery,
    settings: Settings = Depends(get_settings),
):
    """Search for job listings across multiple job boards."""
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
        except ValueError as e:
            if ai_config_explicit:
                raise HTTPException(status_code=400, detail=f"AI settings error: {e}")

        interpreted = body
        if ai_connection and body.user_context:
            try:
                interpreted = await interpret_job_query(
                    body.query,
                    ai_connection["api_key"],
                    body.user_context,
                    body.ai_model or settings.ai_model,
                    ai_connection["base_url"],
                )
                interpreted.max_results = body.max_results
            except Exception as e:
                print(f"Job query interpretation failed, using raw query: {e}")

        jobs, query_used = await search_jobs(
            query=interpreted.query,
            location=interpreted.location or body.location,
            max_results=interpreted.max_results,
        )

        return JobSearchResponse(
            query_used=query_used,
            jobs=jobs,
            total_found=len(jobs),
        )
    except Exception as e:
        print(f"Job search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
