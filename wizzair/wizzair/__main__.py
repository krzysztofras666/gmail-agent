from __future__ import annotations

import argparse
import asyncio
import sys
from dataclasses import replace
from pathlib import Path

from wizzair.config import get_settings
from wizzair.doctor import print_doctor_report, run_doctor
from wizzair.email import send_delta_digest, send_digest
from wizzair.render import print_json, print_scan_result
from wizzair.scan_args import add_scan_args, apply_scan_args
from wizzair.scanner import login_and_save_session, scan_multipass
from wizzair.snapshot import compare_flights, load_morning_snapshot, save_morning_snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wizzair",
        description=(
            "Loguje się do Wizz Multipass i wyszukuje dostępne loty "
            "All You Can Fly z wybranych lotnisk."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser(
        "run",
        help="Zaloguj się i przeskanuj dostępne loty (domyślnie KRK/KTW, dziś + 3 dni)",
    )
    run.add_argument("--json", action="store_true", help="Wydrukuj JSON")
    run.add_argument("--diagnostics", action="store_true", help="Pokaż diagnostykę")
    run.add_argument("--headed", action="store_true", help="Uruchom przeglądarkę z UI")
    add_scan_args(run)
    run.set_defaults(func=cmd_run)

    send = sub.add_parser("send", help="Poranny skan i pełny digest e-mailem (08:00)")
    send.add_argument("--dry-run", action="store_true", help="Wygeneruj HTML bez wysyłki")
    send.add_argument("--from", dest="sender", help="Nadawca")
    send.add_argument("--to", action="append", dest="recipients", help="Odbiorca")
    send.add_argument("--headed", action="store_true")
    add_scan_args(send)
    send.set_defaults(func=cmd_send_morning)

    send_delta = sub.add_parser(
        "send-delta",
        help="Popołudniowy skan i mail tylko ze zmianami względem porannego (13:00)",
    )
    send_delta.add_argument("--dry-run", action="store_true")
    send_delta.add_argument("--from", dest="sender", help="Nadawca")
    send_delta.add_argument("--to", action="append", dest="recipients", help="Odbiorca")
    send_delta.add_argument("--headed", action="store_true")
    send_delta.add_argument(
        "--force",
        action="store_true",
        help="Wyślij mail nawet gdy nie ma zmian",
    )
    add_scan_args(send_delta)
    send_delta.set_defaults(func=cmd_send_delta)

    preview = sub.add_parser("preview-email", help="Zapisz poranny HTML digest na dysk")
    preview.add_argument("--out", default="logs/last_email.html", help="Ścieżka wyjściowa")
    preview.add_argument("--headed", action="store_true")
    add_scan_args(preview)
    preview.set_defaults(func=cmd_preview)

    preview_delta = sub.add_parser("preview-delta", help="Zapisz popołudniowy HTML ze zmianami")
    preview_delta.add_argument("--out", default="logs/last_delta_email.html")
    preview_delta.add_argument("--headed", action="store_true")
    add_scan_args(preview_delta)
    preview_delta.set_defaults(func=cmd_preview_delta)

    auth = sub.add_parser("login", help="Zaloguj się i zapisz sesję przeglądarki (przydatne na Macu)")
    auth.add_argument("--headed", action="store_true", help="Pokaż okno przeglądarki")
    auth.set_defaults(func=cmd_login)

    doctor = sub.add_parser("doctor", help="Sprawdź konfigurację: .env, Gmail, sesja, harmonogram")
    doctor.set_defaults(func=cmd_doctor)

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    settings = apply_scan_args(_with_headed(get_settings(), args), args)
    result = asyncio.run(scan_multipass(settings))
    if args.json:
        print_json(result)
    else:
        print_scan_result(result, show_diagnostics=args.diagnostics)
    return 0


def cmd_send_morning(args: argparse.Namespace) -> int:
    settings = apply_scan_args(_with_headed(get_settings(), args), args)
    if not settings.agent_enabled:
        raise SystemExit(
            "wizzair is disabled (WIZZAIR_AGENT_ENABLED=0). "
            "Re-enable in wizzair/.env or run scripts/enable_agent.sh"
        )
    result = asyncio.run(scan_multipass(settings))
    snapshot_path = save_morning_snapshot(result)
    recipients = _normalize_recipients(args.recipients)
    to_addrs = recipients or settings.email_to
    out = send_digest(
        settings,
        result,
        sender=args.sender,
        recipients=recipients,
        dry_run=args.dry_run,
        slot_label="08:00",
    )
    if args.dry_run:
        print(f"Dry run — e-mail NIE wysłany. Podgląd: {out}")
    else:
        print(f"Wysłano poranny digest do: {', '.join(to_addrs)}")
    print(f"Snapshot poranny: {snapshot_path}")
    print(f"Podgląd HTML: {out}")
    return 0


def cmd_send_delta(args: argparse.Namespace) -> int:
    settings = apply_scan_args(_with_headed(get_settings(), args), args)
    if not settings.agent_enabled:
        raise SystemExit(
            "wizzair is disabled (WIZZAIR_AGENT_ENABLED=0). "
            "Re-enable in wizzair/.env or run scripts/enable_agent.sh"
        )
    baseline = load_morning_snapshot()
    if not baseline:
        print("Brak porannego snapshotu — najpierw uruchom: python -m wizzair send")
        return 1

    result = asyncio.run(scan_multipass(settings))
    delta = compare_flights(baseline, result.flights)
    recipients = _normalize_recipients(args.recipients)
    to_addrs = recipients or settings.email_to

    if not delta.has_changes and not args.force and not args.dry_run:
        print("Brak zmian względem porannego maila — popołudniowy e-mail nie został wysłany.")
        return 0

    out = send_delta_digest(
        settings,
        delta,
        sender=args.sender,
        recipients=recipients,
        dry_run=args.dry_run,
    )
    if args.dry_run:
        print(f"Dry run — e-mail NIE wysłany. Podgląd: {out}")
    elif out is None:
        print("Brak zmian — e-mail nie został wysłany.")
    else:
        print(f"Wysłano popołudniowy digest zmian do: {', '.join(to_addrs)}")
        print(f"Nowe: {len(delta.added)}, zniknęły: {len(delta.removed)}")
        print(f"Podgląd HTML: {out}")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    settings = apply_scan_args(_with_headed(get_settings(), args), args)
    result = asyncio.run(scan_multipass(settings))
    from wizzair.render_html import render_html

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(result, slot_label="08:00"), encoding="utf-8")
    print(f"Zapisano {out}")
    return 0


def cmd_preview_delta(args: argparse.Namespace) -> int:
    settings = apply_scan_args(_with_headed(get_settings(), args), args)
    baseline = load_morning_snapshot()
    if not baseline:
        print("Brak porannego snapshotu — najpierw uruchom: python -m wizzair send --dry-run")
        return 1

    result = asyncio.run(scan_multipass(settings))
    delta = compare_flights(baseline, result.flights)
    from wizzair.render_html import render_delta_html

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_delta_html(delta), encoding="utf-8")
    print(f"Zapisano {out} (+{len(delta.added)} / -{len(delta.removed)})")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    return print_doctor_report(run_doctor())


def cmd_login(args: argparse.Namespace) -> int:
    settings = _with_headed(get_settings(), args)
    if not args.headed:
        settings = replace(settings, headless=False)
    session_path = asyncio.run(login_and_save_session(settings))
    print(f"Zalogowano. Sesja zapisana: {session_path}")
    print("Kolejne uruchomienia mogą używać zapisanej sesji bez ponownego logowania.")
    return 0


def _with_headed(settings, args: argparse.Namespace):
    if getattr(args, "headed", False):
        return replace(settings, headless=False)
    return settings


def _normalize_recipients(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    recipients: list[str] = []
    for value in values:
        recipients.extend(part.strip() for part in value.split(",") if part.strip())
    return recipients


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
