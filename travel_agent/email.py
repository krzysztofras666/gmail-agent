from __future__ import annotations

import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from travel_agent.config import Settings
from travel_agent.render_html import build_subject, render_html, render_plain_text
from travel_agent.models import RunResult


def send_digest(
    settings: Settings,
    result: RunResult,
    *,
    sender: str | None = None,
    recipients: list[str] | None = None,
    dry_run: bool = False,
    out_path: Path | None = None,
) -> Path:
    from_addr = sender or settings.email_from
    to_addrs = recipients or settings.email_to
    html = render_html(result)
    plain = render_plain_text(result)
    subject = build_subject(result)

    if out_path is None:
        out_path = Path("logs/last_email.html")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    if dry_run:
        return out_path

    if not settings.email_enabled:
        raise RuntimeError(
            "Outbound email is disabled (TRAVEL_EMAIL_ENABLED=0). "
            "Use --dry-run to render a preview without sending."
        )

    service = _gmail_service(settings, from_addr)
    message = MIMEMultipart("alternative")
    message["To"] = ", ".join(to_addrs)
    message["From"] = from_addr
    message["Subject"] = subject
    message.attach(MIMEText(plain, "plain", "utf-8"))
    message.attach(MIMEText(html, "html", "utf-8"))

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return out_path


def find_gmail_token_path(settings: Settings, sender: str) -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    candidates = [
        Path(settings.gmail_token_dir) / sender / "token.json",
        Path(settings.gmail_token_dir) / "accounts" / sender / "token.json",
        repo_root.parent / "gmail-agent" / "accounts" / sender / "token.json",
        repo_root / "accounts" / sender / "token.json",
    ]
    for path in candidates:
        if path.exists():
            return path

    tried = "\n".join(f"  - {path}" for path in candidates)
    raise RuntimeError(
        f"No Gmail token for {sender}. Looked in:\n{tried}\n\n"
        "Authenticate first:\n"
        f"  cd ~/gmail-agent && python -m gmail_agent auth --account {sender}\n\n"
        "If tokens live elsewhere, set GMAIL_TOKEN_DIR in .env"
    )


def _gmail_service(settings: Settings, sender: str):
    token_path = find_gmail_token_path(settings, sender)
    creds = Credentials.from_authorized_user_file(str(token_path))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds, cache_discovery=False)
