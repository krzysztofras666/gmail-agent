from __future__ import annotations

import re
from html import unescape

STRIP_TAGS = ("script", "style", "nav", "header", "footer", "noscript", "svg", "iframe")


def flatten_rss(xml: str) -> str:
    items = re.findall(r"<item>(.*?)</item>", xml, flags=re.IGNORECASE | re.DOTALL)
    if not items:
        items = re.findall(r"<entry>(.*?)</entry>", xml, flags=re.IGNORECASE | re.DOTALL)
    chunks: list[str] = []
    for item in items:
        title = _tag_text(item, "title")
        link = _tag_text(item, "link") or _attr_text(item, "link", "href")
        description = _tag_text(item, "description") or _tag_text(item, "summary") or _tag_text(item, "content")
        pub_date = (
            _tag_text(item, "pubDate")
            or _tag_text(item, "published")
            or _tag_text(item, "updated")
        )
        author = _tag_text(item, "author") or _tag_text(item, "dc:creator")
        chunks.append(
            "\n".join(
                part
                for part in (title, pub_date, author, link, _strip_html(description))
                if part
            )
        )
    return "\n\n".join(chunks)


def clean_content(text: str, *, kind: str = "rss", max_chars: int = 18000) -> str:
    if kind == "rss":
        cleaned = flatten_rss(text)
    elif kind == "html":
        cleaned = text
        for tag in STRIP_TAGS:
            cleaned = re.sub(
                rf"<{tag}\b[^>]*>.*?</{tag}>",
                " ",
                cleaned,
                flags=re.IGNORECASE | re.DOTALL,
            )
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        cleaned = unescape(cleaned)
    else:
        cleaned = text

    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[:max_chars]
    return cleaned


def _tag_text(fragment: str, tag: str) -> str:
    match = re.search(
        rf"<{tag}[^>]*>(.*?)</{tag}>",
        fragment,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    return _strip_html(match.group(1))


def _attr_text(fragment: str, tag: str, attr: str) -> str:
    match = re.search(
        rf"<{tag}[^>]*\b{attr}=['\"]([^'\"]+)['\"]",
        fragment,
        flags=re.IGNORECASE,
    )
    return match.group(1) if match else ""


def _strip_html(value: str) -> str:
    value = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", value, flags=re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return unescape(re.sub(r"\s+", " ", value)).strip()
