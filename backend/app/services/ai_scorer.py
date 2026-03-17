import json
from openai import AsyncOpenAI

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

from app.models.schemas import LinkedInProfile


SCORING_PROMPT = """You are an expert networking advisor helping someone explore career opportunities.

The user is looking for people to do informational interviews with. Given their search intent and a list of LinkedIn profiles found via search, score each profile's relevance for an informational interview on a scale of 0-100 and provide a brief reason.

Consider:
- How well their role/headline matches the user's area of interest
- Seniority level (mid-career professionals are often most helpful for informational interviews)
- Whether they seem approachable (e.g., active on LinkedIn, diverse experience)

User's search intent: {query}

Profiles to score:
{profiles}

Respond with a JSON array of objects, each with:
- "index": the profile's index in the list (0-based)
- "score": relevance score 0-100
- "reason": one sentence explaining why they're relevant or not

Return ONLY the JSON array, no other text."""


async def score_profiles(
    profiles: list[LinkedInProfile],
    query: str,
    api_key: str,
) -> list[LinkedInProfile]:
    """Score profiles using an LLM for relevance to the user's networking goals."""
    if not profiles or not api_key:
        return profiles

    profiles_text = "\n".join(
        f"{i}. Name: {p.name} | Headline: {p.headline or 'N/A'} | "
        f"Location: {p.location or 'N/A'} | Snippet: {p.snippet or 'N/A'}"
        for i, p in enumerate(profiles)
    )

    client = AsyncOpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)

    try:
        response = await client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {
                    "role": "user",
                    "content": SCORING_PROMPT.format(
                        query=query, profiles=profiles_text
                    ),
                }
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "[]"
        parsed = json.loads(content)

        scores = parsed if isinstance(parsed, list) else parsed.get("scores", parsed.get("results", []))

        for item in scores:
            idx = item.get("index", -1)
            if 0 <= idx < len(profiles):
                profiles[idx].relevance_score = item.get("score", 0)
                profiles[idx].relevance_reason = item.get("reason", "")

        profiles.sort(key=lambda p: p.relevance_score or 0, reverse=True)

    except Exception as e:
        print(f"AI scoring failed (results returned unscored): {e}")

    return profiles
