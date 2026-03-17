from notion_client import AsyncClient

from app.models.schemas import SaveContactRequest


async def get_database_schema(api_key: str, database_id: str) -> dict:
    """Fetch the Notion database schema to understand its properties."""
    client = AsyncClient(auth=api_key)
    db = await client.databases.retrieve(database_id=database_id)
    return {
        "title": db.get("title", [{}])[0].get("plain_text", ""),
        "properties": {
            name: {
                "type": prop["type"],
                "id": prop["id"],
            }
            for name, prop in db.get("properties", {}).items()
        },
    }


async def save_contact_to_notion(
    api_key: str,
    database_id: str,
    contact: SaveContactRequest,
    property_mapping: dict | None = None,
) -> dict:
    """Save a contact to the Notion database.

    property_mapping maps our field names to the actual Notion property names.
    If not provided, uses sensible defaults.
    """
    client = AsyncClient(auth=api_key)

    mapping = property_mapping or {
        "name": "Name",
        "headline": "Title/Role",
        "location": "Location",
        "linkedin_url": "LinkedIn URL",
        "status": "Status",
        "relevance_score": "Relevance Score",
        "notes": "Notes",
    }

    properties: dict = {}

    if mapping.get("name"):
        properties[mapping["name"]] = {
            "title": [{"text": {"content": contact.name}}]
        }

    if contact.headline and mapping.get("headline"):
        properties[mapping["headline"]] = {
            "rich_text": [{"text": {"content": contact.headline}}]
        }

    if contact.location and mapping.get("location"):
        properties[mapping["location"]] = {
            "rich_text": [{"text": {"content": contact.location}}]
        }

    if contact.linkedin_url and mapping.get("linkedin_url"):
        properties[mapping["linkedin_url"]] = {
            "url": contact.linkedin_url
        }

    if contact.status and mapping.get("status"):
        properties[mapping["status"]] = {
            "select": {"name": contact.status.value}
        }

    if contact.relevance_score is not None and mapping.get("relevance_score"):
        properties[mapping["relevance_score"]] = {
            "number": contact.relevance_score
        }

    notes_content = ""
    if contact.relevance_reason:
        notes_content += f"AI Assessment: {contact.relevance_reason}\n"
    if contact.notes:
        notes_content += contact.notes

    if notes_content and mapping.get("notes"):
        properties[mapping["notes"]] = {
            "rich_text": [{"text": {"content": notes_content.strip()}}]
        }

    page = await client.pages.create(
        parent={"database_id": database_id},
        properties=properties,
    )

    return {"id": page["id"], "url": page["url"]}


async def get_saved_contacts(
    api_key: str,
    database_id: str,
) -> list[dict]:
    """Fetch existing contacts from the Notion database."""
    client = AsyncClient(auth=api_key)

    results = await client.databases.query(database_id=database_id)

    contacts = []
    for page in results.get("results", []):
        props = page.get("properties", {})
        contact = {"id": page["id"], "url": page["url"]}

        for prop_name, prop_value in props.items():
            ptype = prop_value.get("type")
            if ptype == "title":
                texts = prop_value.get("title", [])
                contact[prop_name] = texts[0].get("plain_text", "") if texts else ""
            elif ptype == "rich_text":
                texts = prop_value.get("rich_text", [])
                contact[prop_name] = texts[0].get("plain_text", "") if texts else ""
            elif ptype == "url":
                contact[prop_name] = prop_value.get("url", "")
            elif ptype == "select":
                sel = prop_value.get("select")
                contact[prop_name] = sel.get("name", "") if sel else ""
            elif ptype == "number":
                contact[prop_name] = prop_value.get("number")

        contacts.append(contact)

    return contacts
