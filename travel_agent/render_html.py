from __future__ import annotations

from datetime import date
from html import escape
from itertools import groupby

from travel_agent.models import RunResult, TravelOffer
from travel_agent.urls import resolve_offer_url


def build_subject(result: RunResult) -> str:
    destinations = {offer.destination for offer in result.offers}
    today = date.today().isoformat()
    return (
        f"Tanie wakacje — {today} "
        f"({len(destinations)} kierunków, {len(result.offers)} ofert)"
    )


def render_html(result: RunResult) -> str:
    subject = build_subject(result)
    today = date.today().strftime("%d.%m.%Y")
    sections = _render_sections(result.offers)
    if not sections:
        sections = (
            '<p style="margin:0;color:#5b6472;font-size:15px;">'
            "Dziś nie znaleźliśmy ofert z terminem wyjazdu od jutra. "
            "Spróbuj ponownie jutro o 08:00."
            "</p>"
        )

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#eef4f8;font-family:Arial,Helvetica,sans-serif;color:#1f2933;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef4f8;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:680px;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 10px 30px rgba(15,52,96,0.12);">
          <tr>
            <td style="background:linear-gradient(135deg,#0b6e9a 0%,#0f9b8e 100%);padding:28px 28px 24px;color:#ffffff;">
              <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.85;margin-bottom:8px;">
                Travel Agent
              </div>
              <h1 style="margin:0 0 8px;font-size:28px;line-height:1.2;font-weight:700;">
                Tanie wakacje na dziś
              </h1>
              <p style="margin:0;font-size:15px;line-height:1.5;opacity:0.95;">
                Najtańsze oferty z polskich portali · tylko wyjazdy od jutra · {escape(today)}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 28px 8px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  {_stat_cell(str(len({o.destination for o in result.offers})), "kierunków")}
                  {_stat_cell(str(len(result.offers)), "ofert")}
                  {_stat_cell("08:00", "codziennie")}
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 28px;">
              {sections}
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 28px;">
              <p style="margin:0;font-size:12px;line-height:1.6;color:#7b8794;">
                Oferty pochodzą z: esky.pl, itaka.pl, r.pl, travelplanet.pl,
                super-last-minute.pl, kanalwyjazdowy.pl i innych skonfigurowanych portali.
                Kliknij nazwę kierunku lub przycisk, aby przejść do oferty.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def render_plain_text(result: RunResult) -> str:
    lines = [build_subject(result), ""]
    for offer in result.offers:
        dates = _format_dates(offer)
        link = resolve_offer_url(offer)
        lines.append(
            f"- {offer.destination} | {dates} | {offer.price:.0f} {offer.currency} | "
            f"{offer.source} | {link}"
        )
    if not result.offers:
        lines.append("Brak ofert w tym przebiegu.")
    return "\n".join(lines)


def _stat_cell(value: str, label: str) -> str:
    return (
        "<td width='33%' style='padding:8px;'>"
        "<div style='background:#f7fbfd;border:1px solid #dbe7ef;border-radius:12px;padding:14px;text-align:center;'>"
        f"<div style='font-size:24px;font-weight:700;color:#0b6e9a;'>{escape(value)}</div>"
        f"<div style='font-size:12px;color:#5b6472;margin-top:4px;'>{escape(label)}</div>"
        "</div></td>"
    )


def _render_sections(offers: list[TravelOffer]) -> str:
    sorted_offers = sorted(offers, key=lambda o: (o.destination.casefold(), o.departure_date, o.price))
    sections: list[str] = []
    for destination, group in groupby(sorted_offers, key=lambda o: o.destination):
        group_offers = list(group)
        cards = "\n".join(_render_offer_card(offer) for offer in group_offers)
        sections.append(
            "<div style='margin-bottom:22px;'>"
            f"<h2 style='margin:0 0 12px;font-size:18px;color:#12344d;'>{escape(destination)}</h2>"
            f"{cards}"
            "</div>"
        )
    return "\n".join(sections)


def _render_offer_card(offer: TravelOffer) -> str:
    link = resolve_offer_url(offer)
    dates = _format_dates(offer)
    price = f"{offer.price:,.0f}".replace(",", " ")
    nights = f"{offer.nights} nocy · " if offer.nights else ""
    title = escape(offer.title) if offer.title else escape(offer.destination)
    notes = (
        f"<div style='margin-top:8px;font-size:13px;color:#5b6472;'>{escape(offer.notes)}</div>"
        if offer.notes
        else ""
    )

    return (
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' "
        "style='margin-bottom:12px;border:1px solid #dbe7ef;border-radius:14px;background:#fbfdff;'>"
        "<tr><td style='padding:16px 18px;'>"
        f"<div style='font-size:16px;font-weight:700;margin-bottom:6px;'>"
        f"<a href='{escape(link)}' style='color:#0b6e9a;text-decoration:none;'>{title}</a>"
        "</div>"
        f"<div style='font-size:14px;color:#334155;margin-bottom:10px;'>{escape(dates)}</div>"
        f"<div style='font-size:13px;color:#5b6472;margin-bottom:12px;'>{nights}{escape(offer.source)}</div>"
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0'><tr>"
        f"<td style='font-size:22px;font-weight:700;color:#0f9b8e;'>{price} {escape(offer.currency)}</td>"
        "<td align='right'>"
        f"<a href='{escape(link)}' style='display:inline-block;background:#0b6e9a;color:#ffffff;"
        "text-decoration:none;font-size:13px;font-weight:700;padding:10px 16px;border-radius:999px;'>"
        "Zobacz ofertę →</a>"
        "</td></tr></table>"
        f"{notes}"
        "</td></tr></table>"
    )


def _format_dates(offer: TravelOffer) -> str:
    if offer.return_date:
        return f"{offer.departure_date} → {offer.return_date}"
    return offer.departure_date
