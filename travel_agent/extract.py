from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from travel_agent.config import Settings
from travel_agent.models import TravelOffer
from travel_agent.sites import Site

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "offers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string"},
                    "return_date": {"type": "string"},
                    "price": {"type": "number"},
                    "currency": {"type": "string"},
                    "nights": {"type": ["integer", "null"]},
                    "title": {"type": "string"},
                    "notes": {"type": "string"},
                    "url": {"type": "string"},
                },
                "required": [
                    "destination",
                    "departure_date",
                    "return_date",
                    "price",
                    "currency",
                    "nights",
                    "title",
                    "notes",
                    "url",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["offers"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You extract concrete travel offers from messy Polish travel-site text.
Return only valid JSON matching the schema.
Rules:
- Skip banners, navigation, and generic marketing copy.
- Never invent dates or prices that are not present in the text.
- Only include offers whose departure date is tomorrow or later; skip past departures.
- Use ISO dates (YYYY-MM-DD) when possible.
- url must be a full https:// link copied from the source when a direct offer URL exists; otherwise use an empty string.
- destination should be "Country, City/Region" when both are known.
- currency should be a 3-letter code (usually PLN).
- If no real offers are present, return {"offers": []}.
"""


def extract_offers(
    settings: Settings,
    site: Site,
    cleaned_text: str,
) -> list[TravelOffer]:
    if not cleaned_text.strip():
        return []

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_model,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "travel_offers",
                "strict": True,
                "schema": EXTRACTION_SCHEMA,
            },
        },
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Site: {site.name}\n"
                    f"Source id: {site.id}\n\n"
                    f"Text:\n{cleaned_text}"
                ),
            },
        ],
        temperature=0,
    )
    content = response.choices[0].message.content or "{}"
    payload = json.loads(content)
    return [_to_offer(item, site) for item in payload.get("offers", [])]


from travel_agent.urls import resolve_offer_url


def _to_offer(item: dict[str, Any], site: Site) -> TravelOffer:
    offer = TravelOffer(
        destination=item["destination"].strip(),
        departure_date=item["departure_date"].strip(),
        return_date=item.get("return_date", "").strip(),
        price=float(item["price"]),
        currency=item.get("currency", "PLN").strip() or "PLN",
        nights=item.get("nights"),
        title=item.get("title", "").strip(),
        notes=item.get("notes", "").strip(),
        source=site.name,
        source_id=site.id,
        url=item.get("url", "").strip(),
    )
    return TravelOffer(
        destination=offer.destination,
        departure_date=offer.departure_date,
        return_date=offer.return_date,
        price=offer.price,
        currency=offer.currency,
        nights=offer.nights,
        title=offer.title,
        notes=offer.notes,
        source=offer.source,
        source_id=offer.source_id,
        url=resolve_offer_url(offer),
    )
