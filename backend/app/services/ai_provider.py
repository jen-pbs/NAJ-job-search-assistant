from app.config import Settings


DEFAULT_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
}


def resolve_ai_connection(
    settings: Settings,
    ai_provider: str | None = None,
    ai_api_key: str | None = None,
    ai_base_url: str | None = None,
) -> dict[str, str]:
    provider_raw = (ai_provider or "groq").strip().lower()
    provider = provider_raw or "groq"

    provided_key = (ai_api_key or "").strip()
    api_key = provided_key

    if not api_key and provider == "groq":
        api_key = (settings.groq_api_key or "").strip()

    if not api_key:
        raise ValueError("API key is required for the selected provider.")

    if provider in DEFAULT_BASE_URLS:
        base_url = (ai_base_url or DEFAULT_BASE_URLS[provider]).strip()
    else:
        base_url = (ai_base_url or "").strip()
        if not base_url:
            raise ValueError(
                "Unknown provider. Please provide a base URL for this provider."
            )

    return {
        "provider": provider,
        "api_key": api_key,
        "base_url": base_url,
    }
