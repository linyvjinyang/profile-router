"""Decide which profile a link opens in."""

from __future__ import annotations

from fnmatch import fnmatch
from urllib.parse import urlsplit

from .config import Account, Rule


def host_of(url: str) -> str:
    if "://" not in url:
        url = "https://" + url
    return (urlsplit(url).hostname or "").lower()


def matches(pattern: str, host: str) -> bool:
    pattern = pattern.strip().lower()
    if not pattern or not host:
        return False
    if any(ch in pattern for ch in "*?["):
        return fnmatch(host, pattern)
    return host == pattern or host.endswith("." + pattern)


def route(url: str, rules: list[Rule]) -> str | None:
    """card_id of the most specific matching rule (longest pattern wins), or None."""
    host = host_of(url)
    hits = [r for r in rules if matches(r.pattern, host)]
    if not hits:
        return None
    return max(hits, key=lambda r: len(r.pattern.strip("*?. "))).card


def accounts_for(url: str, accounts: list[Account]) -> list[Account]:
    """Accounts on the site this link belongs to (the most specific site wins, e.g. mail.google.com over google.com)."""
    host = host_of(url)
    hits = [a for a in accounts if matches(a.site, host)]
    if not hits:
        return []
    best = max(len(a.site.strip("*?. ")) for a in hits)
    return [a for a in hits if len(a.site.strip("*?. ")) == best]


def account_url(a: Account) -> str:
    return normalize(a.url) if a.url else normalize(a.site.strip("*.") + "/")


def account_urls(a: Account) -> list[str]:
    """What switching to an account opens: its saved pages, or else its start page."""
    return [normalize(u) for u in a.pages if u.strip()] or [account_url(a)]


def normalize(url: str) -> str:
    url = url.strip()
    if url and "://" not in url and not url.startswith(("about:", "chrome:", "edge:", "file:")):
        url = "https://" + url
    return url
