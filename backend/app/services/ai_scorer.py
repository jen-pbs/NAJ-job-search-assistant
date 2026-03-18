import json
from openai import AsyncOpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

from app.models.schemas import LinkedInProfile


SCORING_PROMPT = """You are an expert networking advisor. The user is exploring career opportunities and wants to find the best people for informational interviews.

User's search intent: "{query}"

Below are LinkedIn profiles found via search. For each person, I've included whatever information was available from their public LinkedIn page (experience, education, about section). Some profiles have rich data, others only have a name and headline.

Your job:
1. Score each profile 0-100 for how valuable an informational interview with them would be
2. Write 2-3 sentences explaining WHY this person is or isn't a good match. Be specific -- reference their actual experience, role transitions, companies, or skills.

Scoring criteria:
- Role relevance: Does their work relate to what the user is looking for?
- Experience depth: Do they have meaningful experience to share insights about the field?
- Approachability: Mid-career professionals and those with diverse paths are often most helpful
- Career path: Did they transition into this field? That perspective is especially valuable.
- Company diversity: Experience at well-known companies or in relevant industries adds value

Profiles:
{profiles}

Return a JSON object with a "scores" key containing an array. Each item must have:
- "index": profile index (0-based)
- "score": 0-100
- "reason": 2-3 sentences explaining your reasoning, referencing specific details from their profile

Be direct and honest. If a profile doesn't seem relevant, say so and give a low score."""


def _build_profile_text(i: int, profile: LinkedInProfile, enrichment: dict | None) -> str:
    """Build descriptive text for a single profile."""
    lines = [f"--- Profile #{i} ---"]
    lines.append(f"Name: {profile.name}")
    
    if enrichment and enrichment.get("enriched"):
        if enrichment.get("headline"):
            lines.append(f"Headline: {enrichment['headline']}")
        elif profile.headline:
            lines.append(f"Headline: {profile.headline}")

        if enrichment.get("location"):
            lines.append(f"Location: {enrichment['location']}")
        elif profile.location:
            lines.append(f"Location: {profile.location}")

        if enrichment.get("experience_text"):
            lines.append(f"Experience: {enrichment['experience_text']}")

        if enrichment.get("education_text"):
            lines.append(f"Education: {enrichment['education_text']}")

        if enrichment.get("description"):
            lines.append(f"Profile summary: {enrichment['description']}")
    else:
        if profile.headline:
            lines.append(f"Headline: {profile.headline}")
        if profile.location:
            lines.append(f"Location: {profile.location}")
        if profile.snippet:
            lines.append(f"Search snippet: {profile.snippet}")
        lines.append("(Limited data -- public profile not fully accessible)")

    return "\n".join(lines)


async def score_profiles(
    profiles: list[LinkedInProfile],
    query: str,
    api_key: str,
    enrichments: list[dict] | None = None,
) -> list[LinkedInProfile]:
    """Score profiles using Groq with enriched profile data."""
    if not profiles or not api_key:
        return profiles

    profiles_text = "\n\n".join(
        _build_profile_text(i, p, enrichments[i] if enrichments and i < len(enrichments) else None)
        for i, p in enumerate(profiles)
    )

    client = AsyncOpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        scores = parsed.get("scores", parsed if isinstance(parsed, list) else [])

        for item in scores:
            idx = item.get("index", -1)
            if 0 <= idx < len(profiles):
                profiles[idx].relevance_score = item.get("score", 0)
                profiles[idx].relevance_reason = item.get("reason", "")

        profiles.sort(key=lambda p: p.relevance_score or 0, reverse=True)

    except Exception as e:
        print(f"AI scoring failed (results returned unscored): {e}")

    return profiles
