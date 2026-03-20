import json
from openai import AsyncOpenAI

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

from app.models.schemas import LinkedInProfile
from app.services.multi_search import MergedProfile


SCORING_PROMPT = """You are an expert networking advisor helping a user find people for informational interviews.

USER'S EXACT SEARCH QUERY: "{query}"

Read the user's query carefully. Extract their specific requirements:
- What field or role are they interested in? (e.g. HEOR, health economics, RWE)
- What background or career path are they looking for? (e.g. transitioned from academia, PhD background, came from consulting)
- What location, if any? (e.g. San Francisco Bay area)
- What seniority or company type? (e.g. director level, pharma, biotech)

These specific requirements MUST drive your scoring. A profile that meets the user's specific criteria scores high. One that is in the right field but misses the key criteria (e.g. has no academic background when the user asked for academia-to-industry transitions) scores lower.

Profiles to evaluate:
{profiles}

For each profile:
1. Score 0-100 based on how well they match the user's SPECIFIC query (not just general field relevance)
2. Write 2-3 sentences explaining the match. Be explicit: does this person meet the specific requirements in the query? If the user asked for people who transitioned from academia, say whether this person did. If a location was specified, say whether they're in it. Reference actual details from their profile.

Also extract:
3. "company": current company name. Null only if truly unknown.
4. "role": current job title. Null only if unknown.
5. "field": one of: "HEOR", "RWE", "Medical affairs", "Health Policy", "Neuroscience", "Genetic medicine", "Mental Health", "Multidisciplinary". Null if none fit.
6. "company_type": one of: "Biotech", "Biopharmaceutic", "Venture Capital", "Academia". Null if none fit.

Return a JSON object with a "scores" array. Each item MUST have:
- "index": 0-based profile index
- "name": person's full name (copied exactly)
- "score": 0-100
- "reason": 2-3 sentences. Start with the person's name. Explicitly address whether they meet the user's specific criteria.
- "company": extracted company or null
- "role": extracted title or null
- "field": field classification or null
- "company_type": company type or null

CRITICAL: Do NOT mix up profiles. Start each reason with the person's name."""


def _apply_scores(profiles: list[LinkedInProfile], scores: list[dict]) -> list[LinkedInProfile]:
    """Apply AI scores to profiles with name-based cross-validation."""
    # Build name->index lookup for correction
    name_to_idx: dict[str, int] = {}
    for i, p in enumerate(profiles):
        name_to_idx[p.name.lower().strip()] = i

    for item in scores:
        idx = item.get("index", -1)
        response_name = (item.get("name") or "").lower().strip()

        # Validate: does the name in the response match the profile at this index?
        if 0 <= idx < len(profiles):
            expected_name = profiles[idx].name.lower().strip()
            if response_name and expected_name not in response_name and response_name not in expected_name:
                # Name mismatch -- try to find the correct profile by name
                corrected_idx = None
                for known_name, known_idx in name_to_idx.items():
                    if response_name in known_name or known_name in response_name:
                        corrected_idx = known_idx
                        break
                if corrected_idx is not None:
                    print(f"[Scorer] Index correction: {idx} -> {corrected_idx} for '{response_name}'")
                    idx = corrected_idx

        if 0 <= idx < len(profiles):
            profiles[idx].relevance_score = item.get("score", 0)
            profiles[idx].relevance_reason = item.get("reason", "")
            profiles[idx].company = item.get("company") or profiles[idx].company
            profiles[idx].role_title = item.get("role") or profiles[idx].role_title
            profiles[idx].field = item.get("field")
            profiles[idx].company_type = item.get("company_type")

    profiles.sort(key=lambda p: p.relevance_score or 0, reverse=True)
    return profiles


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
        existing = "\n".join(lines)
        if snippet[:60] not in existing and "[LinkedIn]" not in snippet:
            lines.append(f"Search snippet: {snippet[:300]}")

    # Open web bio data (conference bios, press releases, Crunchbase)
    if profile.web_bio_data:
        wd = profile.web_bio_data
        if wd.get("bio_text"):
            lines.append(f"Professional bio: {wd['bio_text'][:400]}")
        if wd.get("career_mentions"):
            lines.append(f"Career mentions: {' | '.join(wd['career_mentions'][:3])}")
        if wd.get("companies_mentioned"):
            lines.append(f"Companies associated with: {', '.join(wd['companies_mentioned'][:5])}")
        if wd.get("web_snippets"):
            for ws in wd["web_snippets"][:2]:
                existing = "\n".join(lines)
                if ws[:50] not in existing:
                    lines.append(f"Web info: {ws[:250]}")

    # Google Scholar data
    if profile.scholar_data:
        sd = profile.scholar_data
        if sd.get("publications"):
            pub_titles = [p["title"] for p in sd["publications"][:3]]
            lines.append(f"Google Scholar publications: {'; '.join(pub_titles)}")
        if sd.get("citation_count"):
            lines.append(f"Citation count: {sd['citation_count']}")
        if sd.get("has_scholar_profile"):
            lines.append("Has Google Scholar profile (active researcher)")

    # ORCID data
    if profile.orcid_data:
        od = profile.orcid_data
        if od.get("employment_history"):
            jobs = od["employment_history"]
            job_strs = [
                f"{j.get('role', 'Role')} at {j['organization']} ({j.get('start_year', '?')}-{j.get('end_year', '?')})"
                for j in jobs[:4]
            ]
            lines.append(f"ORCID career timeline: {' -> '.join(job_strs)}")
        if od.get("education"):
            edu_strs = [
                f"{e.get('degree', '')} from {e['institution']}"
                for e in od["education"][:3]
            ]
            lines.append(f"ORCID education: {'; '.join(edu_strs)}")
        if od.get("works_count"):
            lines.append(f"ORCID published works: {od['works_count']}")

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

        profiles = _apply_scores(profiles, scores)

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

        profiles = _apply_scores(profiles, scores)

    except Exception as e:
        print(f"AI scoring failed (results returned unscored): {e}")

    return profiles
