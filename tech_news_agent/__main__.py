from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from tech_news_agent.config import get_settings
from tech_news_agent.email import send_digest
from tech_news_agent.render import print_json, print_run_result
from tech_news_agent.runner import run_agent
from tech_news_agent.sources import SOURCES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tech_news_agent",
        description="Fetch tech headlines from RSS/API sources and email a daily digest.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_sources = sub.add_parser("list-sources", help="Show configured sources and URLs")
    list_sources.set_defaults(func=cmd_list_sources)

    run = sub.add_parser("run", help="Fetch sources and print articles")
    run.add_argument("--source", action="append", dest="sources", help="Limit to source id(s)")
    run.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    run.add_argument(
        "--max-articles",
        type=int,
        default=None,
        help="Keep at most N articles in the final digest",
    )
    run.add_argument("--no-diagnostics", action="store_true", help="Hide per-source status")
    run.set_defaults(func=cmd_run)

    send = sub.add_parser("send", help="Fetch and email the digest")
    send.add_argument("--dry-run", action="store_true", help="Render email without sending")
    send.add_argument("--from", dest="sender", help="Sender email")
    send.add_argument("--to", action="append", dest="recipients", help="Recipient email")
    send.add_argument("--source", action="append", dest="sources")
    send.add_argument("--max-articles", type=int, default=None)
    send.set_defaults(func=cmd_send)

    preview = sub.add_parser("preview-email", help="Render the HTML digest to disk")
    preview.add_argument("--out", required=True, help="Output HTML path")
    preview.add_argument("--source", action="append", dest="sources")
    preview.add_argument("--max-articles", type=int, default=None)
    preview.set_defaults(func=cmd_preview)

    return parser


def cmd_list_sources(_: argparse.Namespace) -> int:
    for source in SOURCES:
        print(f"{source.id:16} {source.name:16} [{source.kind}]")
        for url in source.urls:
            print(f"  - {url}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    settings = get_settings()
    result = asyncio.run(
        run_agent(
            settings,
            source_ids=args.sources,
            max_articles=args.max_articles,
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
            source_ids=args.sources,
            max_articles=args.max_articles,
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
            source_ids=args.sources,
            max_articles=args.max_articles,
        )
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    from tech_news_agent.render_html import render_html

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
