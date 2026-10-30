"""User settings: per-profile card overrides (name, color, home page) and link rules.

Stored as JSON in %APPDATA%\\ProfileRouter\\config.json (override with PROFILE_ROUTER_CONFIG).
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

PALETTE = ("#4F7BE8", "#E8744F", "#3BA776", "#B65FD6", "#D9A21B", "#2BA3B8", "#D9487A", "#6B7A8F")


def config_path() -> Path:
    env = os.environ.get("PROFILE_ROUTER_CONFIG")
    if env:
        return Path(env)
    return Path(os.environ.get("APPDATA", ".")) / "ProfileRouter" / "config.json"


@dataclass
class Card:
    name: str = ""
    color: str = ""
    home: str = ""
    launch_options: list[str] = field(default_factory=list)  # browsers.LAUNCH_OPTIONS keys
    launch_custom: str = ""  # extra switches typed by the user


@dataclass
class Rule:
    pattern: str  # host suffix ("github.com") or glob ("*.example.*")
    card: str  # Profile.card_id


@dataclass
class Account:
    """One login on one site, living in one browser profile (e.g. X 小号 in Chrome Profile 2)."""

    site: str  # host the account belongs to ("x.com"); subdomains match too
    label: str  # what the user calls it ("小号")
    card: str  # Profile.card_id holding the login
    url: str = ""  # page to open when switching; default https://<site>/
    pages: list[str] = field(default_factory=list)  # bookmarked pages opened together when switching


@dataclass
class ExtraProfile:
    """A Chromium profile outside the browser's default data dir (portable browser, test sandbox)."""

    browser: str
    browser_label: str
    exe: str
    user_data_dir: str
    profile_id: str
    name: str


@dataclass
class Config:
    cards: dict[str, Card] = field(default_factory=dict)
    rules: list[Rule] = field(default_factory=list)
    accounts: list[Account] = field(default_factory=list)
    extra_profiles: list[ExtraProfile] = field(default_factory=list)
    ask_unmatched: bool = True  # show the picker for links no rule matches
    fallback: str = ""  # card_id used for unmatched links when ask_unmatched is off
    new_profile_extensions: list[str] = field(default_factory=list)  # extension ids last chosen for new profiles
    sites: list[str] = field(default_factory=list)  # site categories, in display order (may have no accounts yet)
    hidden_rooms: list[str] = field(default_factory=list)  # card_ids the user hid from the room page
    auto_sync: bool = True  # pick up profiles added or renamed in the browsers while the window is open
    language: str = "auto"  # "auto" (system language), "zh", "ja" or "en"

    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        path = path or config_path()
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return cls()
        return cls(
            cards={k: Card(**v) for k, v in raw.get("cards", {}).items()},
            rules=[Rule(**r) for r in raw.get("rules", [])],
            accounts=[Account(**a) for a in raw.get("accounts", [])],
            extra_profiles=[ExtraProfile(**e) for e in raw.get("extra_profiles", [])],
            ask_unmatched=raw.get("ask_unmatched", True),
            fallback=raw.get("fallback", ""),
            new_profile_extensions=raw.get("new_profile_extensions", []),
            sites=raw.get("sites", []),
            hidden_rooms=raw.get("hidden_rooms", []),
            auto_sync=raw.get("auto_sync", True),
            language=raw.get("language", "auto"),
        )

    def save(self, path: Path | None = None) -> None:
        path = path or config_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def site_order(self) -> list[str]:
        """Site categories: the explicit list first, then sites that only appear in accounts."""
        return list(dict.fromkeys([*self.sites, *(a.site for a in self.accounts)]))

    def forget_room(self, card_id: str) -> None:
        """Drop everything registered for a deleted room."""
        self.cards.pop(card_id, None)
        self.accounts = [a for a in self.accounts if a.card != card_id]
        self.rules = [r for r in self.rules if r.card != card_id]
        self.hidden_rooms = [c for c in self.hidden_rooms if c != card_id]
        self.extra_profiles = [e for e in self.extra_profiles if f"{e.browser}:{e.profile_id}" != card_id]
        if self.fallback == card_id:
            self.fallback = ""

    def card(self, card_id: str) -> Card:
        return self.cards.setdefault(card_id, Card())

    def color_for(self, card_id: str, index: int) -> str:
        c = self.cards.get(card_id)
        return c.color if c and c.color else PALETTE[index % len(PALETTE)]
