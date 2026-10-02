from __future__ import annotations

from datetime import date
from html import escape
from itertools import groupby

from wizzair.models import MultipassFlight, ScanResult
from wizzair.snapshot import ScanDelta


def build_subject(result: ScanResult) -> str:
    today = date.today().isoformat()
    routes = {f"{flight.origin}-{flight.destination}" for flight in result.flights}
    return (
        f"Wizz Multipass — {today} "
        f"({len(routes)} tras, {len(result.flights)} lotów)"
    )


def build_delta_subject(delta: ScanDelta) -> str:
    today = date.today().isoformat()
    return (
        f"Wizz Multipass — zmiany {today} "
        f"(+{len(delta.added)} / -{len(delta.removed)})"
    )


def render_html(result: ScanResult, *, slot_label: str = "08:00") -> str:
    subject = build_subject(result)
    today = date.today().strftime("%d.%m.%Y")
    sections = _render_sections(result.flights)
    if not sections:
        sections = (
            '<p style="margin:0;color:#5b6472;font-size:15px;line-height:1.6;">'
            "Dziś nie znaleźliśmy dostępnych lotów All You Can Fly z KRK i KTW "
            "w najbliższych dniach. Spróbuj ponownie przy kolejnym skanie."
            "</p>"
        )

    origins = sorted({flight.origin for flight in result.flights})
    origin_label = ", ".join(origins) if origins else "KRK, KTW"

    return _email_shell(
        subject=subject,
        title="Dostępne loty",
        subtitle=f"Loty z {origin_label} · dziś i 3 najbliższe dni · {today}",
        stat_cells=[
            _stat_cell(str(len(result.flights)), "lotów"),
            _stat_cell(str(len({f'{f.origin}-{f.destination}' for f in result.flights})), "tras"),
            _stat_cell(slot_label, "skan"),
        ],
        body=sections,
        footer=(
            "Loty pochodzą z konta Wizz Multipass. Kliknij „Rezerwuj w Multipass”, "
            "aby dokończyć rezerwację, lub „Zobacz na wizzair.com”, aby sprawdzić lot w standardowej ofercie."
        ),
    )


def render_delta_html(delta: ScanDelta) -> str:
    subject = build_delta_subject(delta)
    today = date.today().strftime("%d.%m.%Y")

    sections: list[str] = []
    if delta.added:
        sections.append(
            "<div style='margin-bottom:24px;'>"
            "<h2 style='margin:0 0 12px;font-size:18px;color:#0f7b4c;'>Nowe loty od rana</h2>"
            f"{_render_sections(delta.added)}"
            "</div>"
        )
    if delta.removed:
        sections.append(
            "<div style='margin-bottom:24px;'>"
            "<h2 style='margin:0 0 12px;font-size:18px;color:#b42318;'>Loty, które zniknęły od rana</h2>"
            f"{_render_removed_sections(delta.removed)}"
            "</div>"
        )

    body = "\n".join(sections)

    return _email_shell(
        subject=subject,
        title="Zmiany od porannego skanu",
        subtitle=f"Porównanie względem maila z 08:00 · {today}",
        stat_cells=[
            _stat_cell(f"+{len(delta.added)}", "nowe"),
            _stat_cell(f"-{len(delta.removed)}", "zniknęły"),
            _stat_cell("13:00", "skan"),
        ],
        body=body,
        footer=(
            "Ten mail zawiera wyłącznie różnice względem porannego podsumowania z 08:00. "
            "Jeśli nie ma zmian, mail nie jest wysyłany."
        ),
    )


def render_plain_text(result: ScanResult) -> str:
    lines = [build_subject(result), ""]
    for flight in result.flights:
        lines.append(_flight_line(flight))
    if not result.flights:
        lines.append("Brak dostępnych lotów w tym przebiegu.")
    return "\n".join(lines)


def render_delta_plain_text(delta: ScanDelta) -> str:
    lines = [build_delta_subject(delta), ""]
    if delta.added:
        lines.append("NOWE:")
        for flight in delta.added:
            lines.append(_flight_line(flight))
    if delta.removed:
        lines.append("")
        lines.append("ZNIKNĘŁY:")
        for flight in delta.removed:
            lines.append(_flight_line(flight))
    return "\n".join(lines)


def _email_shell(
    *,
    subject: str,
    title: str,
    subtitle: str,
    stat_cells: list[str],
    body: str,
    footer: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(subject)}</title>
</head>
<body style="margin:0;padding:0;background:#f6f1f4;font-family:Arial,Helvetica,sans-serif;color:#1f2933;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f1f4;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;background:#ffffff;border-radius:18px;overflow:hidden;box-shadow:0 10px 30px rgba(198,0,126,0.12);">
          <tr>
            <td style="background:linear-gradient(135deg,#c6007e 0%,#7b005f 100%);padding:28px 28px 24px;color:#ffffff;">
              <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;opacity:0.9;margin-bottom:8px;">
                Wizz Multipass · All You Can Fly
              </div>
              <h1 style="margin:0 0 8px;font-size:28px;line-height:1.2;font-weight:700;">
                {escape(title)}
              </h1>
              <p style="margin:0;font-size:15px;line-height:1.5;opacity:0.95;">
                {escape(subtitle)}
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:24px 28px 8px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                  {''.join(stat_cells)}
                </tr>
              </table>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 28px;">
              {body}
            </td>
          </tr>
          <tr>
            <td style="padding:0 28px 28px;">
              <p style="margin:0;font-size:12px;line-height:1.6;color:#7b8794;">
                {escape(footer)}
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _stat_cell(value: str, label: str) -> str:
    return (
        "<td width='33%' style='padding:8px;'>"
        "<div style='background:#fff7fb;border:1px solid #f2d2e4;border-radius:12px;padding:14px;text-align:center;'>"
        f"<div style='font-size:24px;font-weight:700;color:#c6007e;'>{escape(value)}</div>"
        f"<div style='font-size:12px;color:#5b6472;margin-top:4px;'>{escape(label)}</div>"
        "</div></td>"
    )


def _render_sections(flights: list[MultipassFlight]) -> str:
    sorted_flights = sorted(
        flights,
        key=lambda flight: (flight.departure_date, flight.origin, flight.destination),
    )
    sections: list[str] = []
    for departure_date, group in groupby(sorted_flights, key=lambda flight: flight.departure_date):
        group_flights = list(group)
        cards = "\n".join(_render_flight_card(flight) for flight in group_flights)
        sections.append(
            "<div style='margin-bottom:24px;'>"
            f"<h2 style='margin:0 0 12px;font-size:18px;color:#7b005f;'>{escape(departure_date)}</h2>"
            f"{cards}"
            "</div>"
        )
    return "\n".join(sections)


def _render_removed_sections(flights: list[MultipassFlight]) -> str:
    return "\n".join(_render_flight_card(flight, removed=True) for flight in flights)


def _render_flight_card(flight: MultipassFlight, *, removed: bool = False) -> str:
    route = (
        f"{escape(flight.origin_name)} ({escape(flight.origin)}) → "
        f"{escape(flight.destination_name)} ({escape(flight.destination)})"
    )
    times = f"{escape(flight.departure_time)} → {escape(flight.arrival_time)}"
    duration = escape(flight.duration) if flight.duration else "—"
    price = _format_price(flight)
    border = "#f2d2e4"
    background = "#fffbfd"
    if removed:
        border = "#f3d6d4"
        background = "#fff8f7"

    return (
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' "
        f"style='margin-bottom:12px;border:1px solid {border};border-radius:14px;background:{background};'>"
        "<tr><td style='padding:16px 18px;'>"
        f"<div style='font-size:16px;font-weight:700;margin-bottom:6px;color:#12344d;'>{route}</div>"
        f"<div style='font-size:14px;color:#334155;margin-bottom:4px;'>"
        f"<strong>{escape(flight.flight_code)}</strong> · {escape(flight.departure_date)} · {times} · {duration}"
        "</div>"
        f"<div style='font-size:13px;color:#5b6472;margin-bottom:14px;'>{price}</div>"
        + (
            ""
            if removed
            else "<table role='presentation' width='100%' cellpadding='0' cellspacing='0'><tr><td>"
            f"<a href='{escape(flight.multipass_url)}' style='display:inline-block;background:#c6007e;color:#ffffff;"
            "text-decoration:none;font-size:13px;font-weight:700;padding:10px 16px;border-radius:999px;margin-right:8px;'>"
            "Rezerwuj w Multipass →</a>"
            f"<a href='{escape(flight.wizzair_url)}' style='display:inline-block;background:#ffffff;color:#c6007e;"
            "text-decoration:none;font-size:13px;font-weight:700;padding:10px 16px;border-radius:999px;"
            "border:1px solid #e8b3d1;'>Zobacz na wizzair.com</a>"
            "</td></tr></table>"
        )
        + "</td></tr></table>"
    )


def _format_price(flight: MultipassFlight) -> str:
    if flight.price > 0 and flight.currency:
        amount = f"{flight.price:,.2f}".replace(",", " ")
        return f"Cena: {amount} {escape(flight.currency)}"
    return "All You Can Fly"


def _flight_line(flight: MultipassFlight) -> str:
    return (
        f"- {flight.departure_date} | {flight.origin} → {flight.destination} | "
        f"{flight.flight_code} | {flight.departure_time} → {flight.arrival_time} | "
        f"Multipass: {flight.multipass_url} | Wizz: {flight.wizzair_url}"
    )
