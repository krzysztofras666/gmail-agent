from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from travel_agent.config import get_settings
from travel_agent.email import send_digest
from travel_agent.render import print_json, print_run_result
from travel_agent.runner import run_agent
from travel_agent.sites import SITES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="travel_agent",
        description="Scrape Polish travel portals and surface the cheapest deals.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_sites = sub.add_parser("list-sites", help="Show configured sites and URLs")
    list_sites.set_defaults(func=cmd_list_sites)

    run = sub.add_parser("run", help="Scrape sites and print deals")
    run.add_argument("--site", action="append", dest="sites", help="Limit to site id(s)")
    run.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    run.add_argument(
        "--max-per-destination",
        type=int,
        default=None,
        help="Keep N cheapest offers per destination",
    )
    run.add_argument("--no-diagnostics", action="store_true", help="Hide per-site status")
    run.add_argument("--no-browser", action="store_true", help="Use httpx only")
    run.add_argument("--browser-all", action="store_true", help="Fetch every site via Chromium")
    run.set_defaults(func=cmd_run)

    send = sub.add_parser("send", help="Scrape and email the digest")
    send.add_argument("--dry-run", action="store_true", help="Render email without sending")
    send.add_argument("--from", dest="sender", help="Sender email")
    send.add_argument("--to", action="append", dest="recipients", help="Recipient email")
    send.add_argument("--site", action="append", dest="sites")
    send.add_argument("--no-browser", action="store_true")
    send.add_argument("--browser-all", action="store_true")
    send.set_defaults(func=cmd_send)

    preview = sub.add_parser("preview-email", help="Render the HTML digest to disk")
    preview.add_argument("--out", required=True, help="Output HTML path")
    preview.add_argument("--site", action="append", dest="sites")
    preview.add_argument("--no-browser", action="store_true")
    preview.add_argument("--browser-all", action="store_true")
    preview.set_defaults(func=cmd_preview)

    return parser


def _fetch_mode(args: argparse.Namespace) -> str:
    if args.no_browser and args.browser_all:
        raise SystemExit("Use only one of --no-browser or --browser-all")
    if args.no_browser:
        return "http"
    if args.browser_all:
        return "browser"
    return "auto"


def cmd_list_sites(_: argparse.Namespace) -> int:
    for site in SITES:
        print(f"{site.id:18} {site.name}")
        for url in site.urls:
            print(f"  - {url}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = asyncio.run(
        run_agent(
            settings,
            site_ids=args.sites,
            max_per_destination=args.max_per_destination,
            fetch_mode=_fetch_mode(args),
        )
    )
    if args.json:
        print_json(result)
    else:
        print_run_result(result, show_diagnostics=not args.no_diagnostics)
    return 0


def cmd_send(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = asyncio.run(
        run_agent(
            settings,
            site_ids=args.sites,
            fetch_mode=_fetch_mode(args),
        )
    )
    recipients = _normalize_recipients(args.recipients)
    out = send_digest(
        settings,
        result,
        sender=args.sender,
        recipients=recipients,
        dry_run=args.dry_run,
    )
    print(f"Email HTML written to {out}")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = asyncio.run(
        run_agent(
            settings,
            site_ids=args.sites,
            fetch_mode=_fetch_mode(args),
        )
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    from travel_agent.render_html import render_html

    out.write_text(render_html(result), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


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
