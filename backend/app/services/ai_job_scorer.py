import json
from openai import AsyncOpenAI

from app.models.jobs import Job
from app.services.ai_provider import DEFAULT_BASE_URLS


JOB_SCORING_PROMPT = """You are a career advisor helping someone evaluate job listings. Your job is to score how well each job matches the user's background, goals, and preferences.

USER'S SEARCH QUERY: "{query}"

USER'S BACKGROUND AND GOALS:
{user_context}

Read the user's background carefully. Consider:
- What field or industry are they in or targeting? (e.g. HEOR, pharma, biotech, health economics)
- What role level are they at? (entry, mid, senior, director, VP)
- What skills or experience do they have?
- What location do they prefer?
- Are they looking for remote work?
- What kind of company interests them? (startup, big pharma, CRO, academia, consulting)

JOB LISTINGS TO EVALUATE:
{jobs}

For each job, score 0-100 based on how well it fits the user:
- 80-100: Excellent fit -- matches their field, level, and preferences closely
- 60-79: Good fit -- right field but might differ on level, location, or company type
- 40-59: Partial fit -- related field but significant mismatches
- 20-39: Weak fit -- loosely related or wrong level/field
- 0-19: Poor fit -- unrelated to what they're looking for

Write a 1-2 sentence explanation for each job. Be specific and practical:
- Say WHY this job fits or doesn't fit their background
- Mention if the role level matches their experience
- Note salary fit if relevant
- Flag anything they should know (e.g. "requires 10+ years but user is early career")

Return a JSON object with a "scores" array. Each item MUST have:
- "index": 0-based job index
- "score": 0-100
- "reason": 1-2 practical sentences about fit

Return ONLY valid JSON."""


def _format_user_context(user_context: str | None) -> str:
    if not user_context or not user_context.strip():
        return "None provided."
    return user_context.strip()


def _build_job_text(i: int, job: Job) -> str:
    lines = [f"--- Job #{i} ---"]
    lines.append(f"Title: {job.title}")
    if job.company:
        lines.append(f"Company: {job.company}")
    if job.location:
        lines.append(f"Location: {job.location}")
    if job.salary:
        lines.append(f"Salary: {job.salary}")
    if job.is_remote:
        lines.append("Remote: Yes")
    if job.date_posted:
        lines.append(f"Posted: {job.date_posted}")
    if job.description:
        lines.append(f"Description: {job.description}")
    return "\n".join(lines)


async def score_jobs(
    jobs: list[Job],
    query: str,
    api_key: str,
    user_context: str | None = None,
    ai_model: str = "llama-3.3-70b-versatile",
    ai_base_url: str = DEFAULT_BASE_URLS["groq"],
) -> list[Job]:
    if not jobs or not api_key or not user_context or not user_context.strip():
        return jobs

    jobs_text = "\n\n".join(_build_job_text(i, j) for i, j in enumerate(jobs))

    client = AsyncOpenAI(api_key=api_key, base_url=ai_base_url)

    try:
        response = await client.chat.completions.create(
            model=ai_model,
            messages=[
                {
                    "role": "user",
                    "content": JOB_SCORING_PROMPT.format(
                        query=query,
                        user_context=_format_user_context(user_context),
                        jobs=jobs_text,
                    ),
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        scores = parsed.get("scores", parsed if isinstance(parsed, list) else [])

        for item in scores:
            idx = item.get("index", -1)
            if 0 <= idx < len(jobs):
                jobs[idx].relevance_score = item.get("score", 0)
                jobs[idx].relevance_reason = item.get("reason", "")

        jobs.sort(key=lambda j: j.relevance_score or 0, reverse=True)

    except Exception as e:
        print(f"Job AI scoring failed (results returned unscored): {e}")

    return jobs
