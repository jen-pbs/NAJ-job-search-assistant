from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.config import Settings, get_settings
from app.services.notion_client import (
    get_database_schema,
    save_item_to_notion,
    get_saved_items,
    list_user_databases,
)

router = APIRouter(prefix="/api/notion", tags=["notion"])


def _resolve_key(body_key: str | None, settings: Settings) -> str:
    """Use the request-provided key, or fall back to server .env key."""
    key = (body_key or "").strip() or settings.notion_api_key
    if not key:
        raise HTTPException(status_code=400, detail="Notion API key is required. Set NOTION_API_KEY in .env or provide it in the request.")
    return key


class NotionApiKeyBody(BaseModel):
    api_key: str = ""


class SaveItemBody(BaseModel):
    api_key: str = ""
    database_id: str
    fields: dict


class DatabaseSchemaBody(BaseModel):
    api_key: str = ""
    database_id: str


class ListItemsBody(BaseModel):
    api_key: str = ""
    database_id: str


@router.post("/databases")
async def fetch_user_databases(
    body: NotionApiKeyBody,
    settings: Settings = Depends(get_settings),
):
    """List all databases the integration has access to."""
    key = _resolve_key(body.api_key, settings)
    try:
        dbs = await list_user_databases(key)
        return {"databases": dbs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list databases: {e}")


@router.post("/schema")
async def fetch_schema(
    body: DatabaseSchemaBody,
    settings: Settings = Depends(get_settings),
):
    """Get the schema (columns) of a specific Notion database."""
    key = _resolve_key(body.api_key, settings)
    if not body.database_id.strip():
        raise HTTPException(status_code=400, detail="Database ID is required.")
    try:
        schema = await get_database_schema(key, body.database_id.strip())
        return schema
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read schema: {e}")


@router.post("/save")
async def save_item(
    body: SaveItemBody,
    settings: Settings = Depends(get_settings),
):
    """Save an item to any Notion database using dynamic field mapping."""
    key = _resolve_key(body.api_key, settings)
    if not body.database_id.strip():
        raise HTTPException(status_code=400, detail="Database ID is required.")
    if not body.fields:
        raise HTTPException(status_code=400, detail="No fields provided.")
    try:
        result = await save_item_to_notion(
            api_key=key,
            database_id=body.database_id.strip(),
            fields=body.fields,
        )
        return {"status": "saved", "notion_page": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save to Notion: {e}")


@router.post("/items")
async def fetch_items(
    body: ListItemsBody,
    settings: Settings = Depends(get_settings),
):
    """List items from a Notion database."""
    key = _resolve_key(body.api_key, settings)
    if not body.database_id.strip():
        raise HTTPException(status_code=400, detail="Database ID is required.")
    try:
        items = await get_saved_items(key, body.database_id.strip())
        return {"items": items, "total": len(items)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch items: {e}")
