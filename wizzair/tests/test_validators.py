from wizzair.models import Destination
from wizzair.validators import card_matches_route, page_has_no_results


def _sample_card(*lines: str) -> str:
    body = "\n".join(lines)
    return f"{body}\nDodatkowe informacje o locie All You Can Fly z konta Multipass."


def test_card_matches_route_requires_destination_and_price() -> None:
    destination = Destination(code="RHO", label="Rodos (RHO)")
    card = _sample_card(
        "Kraków",
        "Rodos",
        "06:10",
        "10:25",
        "W61234",
        "2h 15m",
        "zł 49.00",
        "WYBIERZ",
    )
    assert card_matches_route(card, destination=destination)


def test_card_rejects_wrong_destination() -> None:
    destination = Destination(code="RHO", label="Rodos (RHO)")
    card = _sample_card(
        "Kraków",
        "Barcelona",
        "06:10",
        "10:25",
        "W61234",
        "2h 15m",
        "zł 49.00",
        "WYBIERZ",
    )
    assert not card_matches_route(card, destination=destination)


def test_card_rejects_missing_price() -> None:
    destination = Destination(code="GOA", label="Genua (GOA)")
    card = _sample_card("Genua", "06:10", "10:25", "W61234", "WYBIERZ")
    assert not card_matches_route(card, destination=destination)


def test_page_has_no_results() -> None:
    assert page_has_no_results("Niestety, nie znaleziono żadnych wyników dla tej trasy.")
