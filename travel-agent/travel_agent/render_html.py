from __future__ import annotations

from datetime import date
from html import escape

from travel_agent.models import RunResult, TravelOffer


def build_subject(result: RunResult) -> str:
    destinations = {offer.destination for offer in result.offers}
    today = date.today().isoformat()
    return (
        f"Tanie wakacje — {today} "
        f"({len(destinations)} kierunków, {len(result.offers)} ofert)"
    )


def render_html(result: RunResult) -> str:
    rows = "\n".join(_render_row(offer) for offer in result.offers)
    if not rows:
        rows = "<tr><td colspan='4'>Brak ofert w tym przebiegu.</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <title>{escape(build_subject(result))}</title>
</head>
<body style="font-family: Arial, sans-serif; color: #222; line-height: 1.4;">
  <h2 style="margin: 0 0 12px;">Tanie wakacje</h2>
  <p style="margin: 0 0 16px; color: #555;">Najtańsze oferty ze skonfigurowanych portali.</p>
  <table cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
    <thead>
      <tr style="background: #f4f4f4;">
        <th align="left">Kierunek</th>
        <th align="left">Termin</th>
        <th align="right">Cena</th>
        <th align="left">Źródło</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>
</body>
</html>"""


def render_plain_text(result: RunResult) -> str:
    lines = [build_subject(result), ""]
    for offer in result.offers:
        dates = offer.return_date and f"{offer.departure_date} → {offer.return_date}" or offer.departure_date
        lines.append(
            f"- {offer.destination} | {dates} | {offer.price:.0f} {offer.currency} | {offer.source}"
        )
    if not result.offers:
        lines.append("Brak ofert w tym przebiegu.")
    return "\n".join(lines)


def _render_row(offer: TravelOffer) -> str:
    dates = offer.return_date and f"{offer.departure_date} → {offer.return_date}" or offer.departure_date
    link_open = f'<a href="{escape(offer.url)}">' if offer.url else ""
    link_close = "</a>" if offer.url else ""
    destination = f"{link_open}{escape(offer.destination)}{link_close}"
    return (
        "<tr>"
        f"<td>{destination}</td>"
        f"<td>{escape(dates)}</td>"
        f"<td align='right'>{offer.price:,.0f} {escape(offer.currency)}</td>"
        f"<td>{escape(offer.source)}</td>"
        "</tr>"
    ).replace(",", " ")
