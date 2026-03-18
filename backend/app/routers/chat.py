from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

from app.config import Settings, get_settings

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

router = APIRouter(prefix="/api/chat", tags=["chat"])

SYSTEM_PROMPT = """You are a career networking assistant. The user is exploring career opportunities (particularly in HEOR, health economics, pharma, and related fields) and is preparing to reach out to professionals for informational interviews.

You help the user by:
- Drafting personalized outreach messages (LinkedIn connection requests, emails, follow-ups)
- Suggesting thoughtful questions to ask during informational interviews
- Analyzing profiles and explaining why someone might be a good connection
- Discussing career strategy and networking approaches
- Helping prepare for conversations

Be concise, warm, and professional. Keep outreach messages short (under 300 characters for LinkedIn connection requests, 3-5 sentences for emails). Always personalize based on the profile data provided.

When profile context is provided, reference specific details from the person's background to make messages authentic, not generic."""


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    profile_context: str | None = None


@router.post("/message")
async def chat_message(
    body: ChatRequest,
    settings: Settings = Depends(get_settings),
):
    """Send a chat message and get a streaming AI response."""
    if not settings.groq_api_key:
        raise HTTPException(status_code=400, detail="Groq API key required for chat.")

    client = AsyncOpenAI(api_key=settings.groq_api_key, base_url=GROQ_BASE_URL)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if body.profile_context:
        messages.append({
            "role": "system",
            "content": f"Current profile context:\n{body.profile_context}",
        })

    for msg in body.messages:
        messages.append({"role": msg.role, "content": msg.content})

    try:
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )

        async def generate():
            async for chunk in response:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        return StreamingResponse(generate(), media_type="text/plain")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {e}")
