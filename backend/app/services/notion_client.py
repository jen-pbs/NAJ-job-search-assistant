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
    """Save a contact to the existing 'People contacted' Notion database.

    Database columns:
      Name (title), Role (rich_text), Company (rich_text),
      Select (select: HEOR, RWE, etc.), Status (status),
      Notes (rich_text), Email (email),
      First-Contact Date (date), Interview/questions Date (date),
      Last contacted (date), Follow-Up Date (date),
      Company Type (select: Biotech, Biopharmaceutic, etc.)
    """
    client = AsyncClient(auth=api_key)

    properties: dict = {}

    # Name (title)
    properties["Name"] = {
        "title": [{"text": {"content": contact.name}}]
    }

    # Role (rich_text) - from headline
    if contact.headline:
        properties["Role"] = {
            "rich_text": [{"text": {"content": contact.headline}}]
        }

    # LinkedIn (url)
    if contact.linkedin_url:
        properties["LinkedIn"] = {
            "url": contact.linkedin_url
        }

    # Company (rich_text) - extract from headline if possible
    if contact.headline and " at " in contact.headline:
        company = contact.headline.split(" at ")[-1].strip()
        properties["Company"] = {
            "rich_text": [{"text": {"content": company}}]
        }
    elif contact.headline and " - " in contact.headline:
        parts = contact.headline.split(" - ")
        if len(parts) >= 2:
            company = parts[-1].strip()
            properties["Company"] = {
                "rich_text": [{"text": {"content": company}}]
            }

    # Location (rich_text) - if available
    if contact.location:
        # No dedicated Location column, add to notes
        pass

    # Notes (rich_text) - AI assessment + user notes
    notes_parts = []
    if contact.relevance_score is not None:
        notes_parts.append(f"Relevance: {contact.relevance_score}/100")
    if contact.relevance_reason:
        notes_parts.append(f"AI: {contact.relevance_reason}")
    if contact.location:
        notes_parts.append(f"Location: {contact.location}")
    if contact.notes:
        notes_parts.append(contact.notes)

    if notes_parts:
        notes_text = "\n".join(notes_parts)
        # Notion rich_text max is 2000 chars
        properties["Notes"] = {
            "rich_text": [{"text": {"content": notes_text[:2000]}}]
        }

    # Select (select) - field/domain like HEOR, RWE, etc.
    if contact.domain:
        properties["Select"] = {
            "select": {"name": contact.domain}
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
            elif ptype == "status":
                sel = prop_value.get("status")
                contact[prop_name] = sel.get("name", "") if sel else ""
            elif ptype == "number":
                contact[prop_name] = prop_value.get("number")
            elif ptype == "email":
                contact[prop_name] = prop_value.get("email", "")
            elif ptype == "date":
                d = prop_value.get("date")
                contact[prop_name] = d.get("start", "") if d else ""

        contacts.append(contact)

    return contacts
