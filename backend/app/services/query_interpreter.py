from openai import AsyncOpenAI
import json

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

from app.models.schemas import SearchQuery


INTERPRET_PROMPT = """You are a search query interpreter. The user wants to find people on LinkedIn for informational interviews.

Given a natural language query, extract structured search parameters for a LinkedIn site: search.

User query: "{query}"

Return a JSON object with:
- "search_terms": the core role/field terms that will find relevant LinkedIn profiles via search engine. Include background context if searchable (e.g. if user wants people who transitioned from academia, include "PhD" or "postdoc" or "research" alongside the field). Keep it to 3-6 words max.
- "location": geographic location if mentioned (city, region, or country), or null
- "companies": list of specific company names if mentioned, or null
- "seniority": seniority level if mentioned (e.g. "Senior", "Director", "VP"), or null
- "alternative_terms": list of 2-3 alternative search phrasings that would find similar people. If the user asked for a career transition (e.g. academia to industry), include alternatives that capture that (e.g. "postdoc HEOR", "PhD health economics industry").

Return ONLY the JSON object."""


async def interpret_query(query: str, api_key: str) -> SearchQuery:
    """Use AI to interpret a natural language query into structured search params."""
    if not api_key:
        return SearchQuery(query=query)

    client = AsyncOpenAI(api_key=api_key, base_url=GROQ_BASE_URL)

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": INTERPRET_PROMPT.format(query=query),
                }
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)

        search_terms = parsed.get("search_terms", query)
        if isinstance(search_terms, list):
            search_terms = " ".join(search_terms)

        return SearchQuery(
            query=str(search_terms),
            location=parsed.get("location"),
            companies=parsed.get("companies"),
            seniority=parsed.get("seniority"),
            alternative_terms=parsed.get("alternative_terms", []),
        )

    except Exception as e:
        print(f"Query interpretation failed, using raw query: {e}")
        return SearchQuery(query=query)
