import json
from openai import AsyncOpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

from app.models.schemas import LinkedInProfile
from app.services.multi_search import MergedProfile


SCORING_PROMPT = """You are an expert networking advisor. The user is exploring career opportunities and wants to find the best people for informational interviews.

User's search intent: "{query}"

Below are LinkedIn profiles found via search. For each person, I've combined data from multiple sources (search engines + their public LinkedIn page). Some profiles have rich data, others only have a name and headline.

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

Also extract and classify each profile:
3. "company": The person's current company name. Extract it from their headline, experience, or description. Just the company name, nothing else. Use null only if truly unknown.
4. "role": Their current job title/role. Extract from headline or experience. Use null only if unknown.
5. "field": Pick the most relevant field from this list ONLY: "HEOR", "RWE", "Medical affairs", "Health Policy", "Neuroscience", "Genetic medicine", "Mental Health", "Multidisciplinary". Use null if none fit.
6. "company_type": Pick from this list ONLY: "Biotech", "Biopharmaceutic", "Venture Capital", "Academia". Use null if none fit or unclear.

Return a JSON object with a "scores" key containing an array. Each item must have:
- "index": profile index (0-based)
- "score": 0-100
- "reason": 2-3 sentences explaining your reasoning, referencing specific details from their profile
- "company": extracted company name or null
- "role": extracted job title or null
- "field": one of the field options above, or null
- "company_type": one of the company type options above, or null

Be direct and honest. If a profile doesn't seem relevant, say so and give a low score."""


def _build_profile_text_merged(i: int, profile: MergedProfile) -> str:
    """Build descriptive text for a merged multi-source profile."""
    lines = [f"--- Profile #{i} ---"]
    lines.append(f"Name: {profile.name}")

    if profile.headline:
        lines.append(f"Headline: {profile.headline}")
    if profile.location:
        lines.append(f"Location: {profile.location}")
    if profile.experience_text:
        lines.append(f"Experience: {profile.experience_text}")
    if profile.education_text:
        lines.append(f"Education: {profile.education_text}")
    if profile.about_text:
        lines.append(f"About: {profile.about_text}")

    # Include public page data
    pub = profile.public_page_data
    if pub.get("description") and pub["description"] not in "\n".join(lines):
        lines.append(f"LinkedIn description: {pub['description'][:400]}")
    if pub.get("visible_text"):
        # Only add if it has new info
        existing = "\n".join(lines)
        visible_clean = pub["visible_text"][:400]
        if visible_clean[:60] not in existing:
            lines.append(f"Public page content: {visible_clean}")

    # Add unique snippets from search engines
    for j, snippet in enumerate(profile.snippets[:3]):
        # Skip if mostly duplicates of what we already have
        existing = "\n".join(lines)
        if snippet[:60] not in existing and "[LinkedIn]" not in snippet:
            lines.append(f"Search snippet: {snippet[:300]}")

    lines.append(f"(Data sources: {', '.join(profile.sources)})")

    return "\n".join(lines)


def _build_profile_text_basic(i: int, profile: LinkedInProfile, enrichment: dict | None) -> str:
    """Build descriptive text for a basic LinkedInProfile (fallback)."""
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


async def score_merged_profiles(
    merged: list[MergedProfile],
    query: str,
    api_key: str,
) -> list[LinkedInProfile]:
    """Score merged multi-source profiles using Groq and convert to LinkedInProfile."""
    if not merged or not api_key:
        return [_merged_to_linkedin(m) for m in merged]

    profiles_text = "\n\n".join(
        _build_profile_text_merged(i, p) for i, p in enumerate(merged)
    )

    client = AsyncOpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    profiles = [_merged_to_linkedin(m) for m in merged]

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
                profiles[idx].company = item.get("company") or profiles[idx].company
                profiles[idx].role_title = item.get("role") or profiles[idx].role_title
                profiles[idx].field = item.get("field")
                profiles[idx].company_type = item.get("company_type")

        profiles.sort(key=lambda p: p.relevance_score or 0, reverse=True)

    except Exception as e:
        print(f"AI scoring failed (results returned unscored): {e}")

    return profiles


def _merged_to_linkedin(m: MergedProfile) -> LinkedInProfile:
    """Convert a MergedProfile to a LinkedInProfile for API response."""
    # Combine all snippets into one rich snippet
    combined_snippet = ""
    if m.snippets:
        combined_snippet = " | ".join(s[:200] for s in m.snippets[:3])

    return LinkedInProfile(
        name=m.name,
        headline=m.headline,
        location=m.location,
        linkedin_url=m.linkedin_url,
        snippet=combined_snippet[:500] if combined_snippet else None,
    )


async def score_profiles(
    profiles: list[LinkedInProfile],
    query: str,
    api_key: str,
    enrichments: list[dict] | None = None,
) -> list[LinkedInProfile]:
    """Score profiles using Groq (legacy interface for backward compat)."""
    if not profiles or not api_key:
        return profiles

    profiles_text = "\n\n".join(
        _build_profile_text_basic(i, p, enrichments[i] if enrichments and i < len(enrichments) else None)
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
                profiles[idx].company = item.get("company") or profiles[idx].company
                profiles[idx].role_title = item.get("role") or profiles[idx].role_title
                profiles[idx].field = item.get("field")
                profiles[idx].company_type = item.get("company_type")

        profiles.sort(key=lambda p: p.relevance_score or 0, reverse=True)

    except Exception as e:
        print(f"AI scoring failed (results returned unscored): {e}")

    return profiles
