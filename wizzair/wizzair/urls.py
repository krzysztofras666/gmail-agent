from __future__ import annotations

from wizzair.config import WALLETS_URL


def wizzair_booking_url(*, origin: str, destination: str, departure_date: str) -> str:
    return (
        "https://www.wizzair.com/pl-pl/booking/select-flight/"
        f"{origin.upper()}/{destination.upper()}/{departure_date}/null/1/0/0/null"
    )


def multipass_wallets_url() -> str:
    return WALLETS_URL
