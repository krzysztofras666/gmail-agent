from __future__ import annotations

from travel_agent.models import TravelOffer


def _offer_key(offer: TravelOffer) -> tuple[str, str, str, int]:
    return (
        offer.destination.casefold(),
        offer.departure_date,
        offer.return_date,
        round(offer.price),
    )


def aggregate_offers(
    offers: list[TravelOffer],
    *,
    max_per_destination: int,
) -> list[TravelOffer]:
    deduped: dict[tuple[str, str, str, int], TravelOffer] = {}
    for offer in offers:
        key = _offer_key(offer)
        existing = deduped.get(key)
        if existing is None or offer.price < existing.price:
            deduped[key] = offer

    by_destination: dict[str, list[TravelOffer]] = {}
    for offer in deduped.values():
        dest_key = offer.destination.casefold()
        by_destination.setdefault(dest_key, []).append(offer)

    result: list[TravelOffer] = []
    for dest_offers in by_destination.values():
        dest_offers.sort(key=lambda o: (o.price, o.departure_date))
        result.extend(dest_offers[:max_per_destination])

    result.sort(key=lambda o: (o.departure_date, o.destination.casefold(), o.price))
    return result
