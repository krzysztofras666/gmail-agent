from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Site:
    id: str
    name: str
    urls: tuple[str, ...]
    is_rss: bool = False


SITES: tuple[Site, ...] = (
    Site("esky", "esky.pl", ("https://www.esky.pl/last-minute", "https://www.esky.pl/")),
    Site("coraltravel", "coraltravel.pl", ("https://www.coraltravel.pl/last-minute", "https://www.coraltravel.pl/")),
    Site("itaka", "itaka.pl", ("https://www.itaka.pl/last-minute", "https://www.itaka.pl/promocje", "https://www.itaka.pl/")),
    Site("fly", "fly.pl", ("https://www.fly.pl/last-minute", "https://www.fly.pl/")),
    Site("lastminute", "pl.lastminute.com", ("https://pl.lastminute.com/deals", "https://pl.lastminute.com/")),
    Site("travelplanet", "travelplanet.pl", ("https://www.travelplanet.pl/last-minute", "https://www.travelplanet.pl/")),
    Site("rpl", "r.pl", ("https://www.r.pl/last-minute", "https://www.r.pl/promocje", "https://www.r.pl/")),
    Site("wakacyjnipiraci", "wakacyjnipiraci.pl", ("https://wakacyjnipiraci.pl/feed",), is_rss=True),
    Site("superlastminute", "super-last-minute.pl", ("https://super-last-minute.pl/",)),
    Site("kanalwyjazdowy", "kanalwyjazdowy.pl", ("https://kanalwyjazdowy.pl/feed/",), is_rss=True),
)

SITES_BY_ID = {site.id: site for site in SITES}


def get_sites(site_ids: list[str] | None = None) -> list[Site]:
    if not site_ids:
        return list(SITES)
    unknown = [site_id for site_id in site_ids if site_id not in SITES_BY_ID]
    if unknown:
        raise ValueError(f"Unknown site id(s): {', '.join(unknown)}")
    return [SITES_BY_ID[site_id] for site_id in site_ids]
