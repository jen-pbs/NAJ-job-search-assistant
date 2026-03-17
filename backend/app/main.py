import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import search

settings = get_settings()

app = FastAPI(
    title="Job Search Assistant",
    description="AI-powered networking and job search tool",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router)


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "search_configured": True,
        "notion_configured": bool(settings.notion_api_key),
        "ai_configured": bool(settings.groq_api_key),
    }
