from __future__ import annotations

import re
from html import unescape

ANTI_BOT_MARKERS = (
    "pardon our interruption",
    "access denied",
    "just a moment",
    "checking your browser",
    "incapsula",
    "cf-browser-verification",
    "captcha",
)

STRIP_TAGS = ("script", "style", "nav", "header", "footer", "noscript", "svg", "iframe")


def looks_like_antibot(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in ANTI_BOT_MARKERS)


def flatten_rss(xml: str) -> str:
    items = re.findall(r"<item>(.*?)</item>", xml, flags=re.IGNORECASE | re.DOTALL)
    chunks: list[str] = []
    for item in items:
        title = _tag_text(item, "title")
        link = _tag_text(item, "link")
        description = _tag_text(item, "description")
        pub_date = _tag_text(item, "pubDate")
        chunks.append(
            "\n".join(
                part
                for part in (title, pub_date, link, _strip_html(description))
                if part
            )
        )
    return "\n\n".join(chunks)


def clean_html(html: str, *, is_rss: bool = False, max_chars: int = 18000) -> str:
    if is_rss:
        text = flatten_rss(html)
    else:
        text = html
        for tag in STRIP_TAGS:
            text = re.sub(
                rf"<{tag}\b[^>]*>.*?</{tag}>",
                " ",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
        text = re.sub(r"<[^>]+>", " ", text)
        text = unescape(text)

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


def _tag_text(fragment: str, tag: str) -> str:
    match = re.search(
        rf"<{tag}[^>]*>(.*?)</{tag}>",
        fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    return _strip_html(match.group(1))


def _strip_html(value: str) -> str:
    value = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", value, flags=re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return unescape(re.sub(r"\s+", " ", value)).strip()
