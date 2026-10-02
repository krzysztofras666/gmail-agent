from __future__ import annotations

from datetime import date, timedelta

from travel_agent.models import TravelOffer


def min_departure_date(*, days_ahead: int = 1) -> date:
    return date.today() + timedelta(days=days_ahead)


def parse_departure_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def is_future_departure(offer: TravelOffer, minimum: date | None = None) -> bool:
    cutoff = minimum or min_departure_date()
    parsed = parse_departure_date(offer.departure_date)
    return parsed is not None and parsed >= cutoff


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
    min_departure: date | None = None,
) -> list[TravelOffer]:
    cutoff = min_departure or min_departure_date()
    offers = [offer for offer in offers if is_future_departure(offer, cutoff)]

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
