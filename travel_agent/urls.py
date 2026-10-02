from __future__ import annotations

from travel_agent.models import TravelOffer
from travel_agent.sites import SITES_BY_ID


def resolve_offer_url(offer: TravelOffer) -> str:
    url = offer.url.strip()
    if url.startswith(("http://", "https://")):
        return url

    site = SITES_BY_ID.get(offer.source_id)
    if site and site.urls:
        return site.urls[0]

    if offer.source:
        return f"https://{offer.source}"

    return "https://example.com"
