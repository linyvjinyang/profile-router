from pathlib import Path

from profile_router.app import decide, room_conflict
from profile_router.browsers import Profile
from profile_router.config import Account, Config, Rule
from profile_router.router import account_url, accounts_for

A = Profile("chrome", "Chrome", Path("chrome.exe"), "chromium", "Default", "A")
B = Profile("chrome", "Chrome", Path("chrome.exe"), "chromium", "Profile 2", "B")
PROFILES = [A, B]


def test_accounts_for_most_specific_site():
    accts = [Account("google.com", "主号", A.card_id), Account("mail.google.com", "工作邮箱", B.card_id)]
    assert [a.label for a in accounts_for("https://mail.google.com/x", accts)] == ["工作邮箱"]
    assert [a.label for a in accounts_for("https://www.google.com", accts)] == ["主号"]
    assert accounts_for("https://x.com", accts) == []


def test_account_url_default():
    assert account_url(Account("x.com", "小号", "c")) == "https://x.com/"
    assert account_url(Account("x.localhost", "小号", "c", "http://x.localhost:8765/")) == "http://x.localhost:8765/"


def test_decide_single_account_opens_directly():
    cfg = Config(accounts=[Account("x.com", "小号", B.card_id)], rules=[Rule("x.com", A.card_id)])
    p, choices, _ = decide("https://x.com/home", cfg, PROFILES)
    assert p == B and choices == []  # accounts take precedence over rules


def test_decide_several_accounts_asks_among_them_only():
    cfg = Config(accounts=[Account("x.com", "主号", A.card_id), Account("x.com", "小号", B.card_id),
                           Account("bilibili.com", "大会员", A.card_id)])
    p, choices, rememberable = decide("https://x.com/i/status/1", cfg, PROFILES)
    assert p is None and not rememberable
    assert [c.title for c in choices] == ["x.com · 主号", "x.com · 小号"]


def test_decide_falls_back_to_rules_then_picker():
    cfg = Config(rules=[Rule("github.com", B.card_id)])
    assert decide("https://github.com", cfg, PROFILES)[0] == B
    p, choices, rememberable = decide("https://example.com", cfg, PROFILES)
    assert p is None and rememberable and len(choices) == 2
    cfg.ask_unmatched, cfg.fallback = False, A.card_id
    assert decide("https://example.com", cfg, PROFILES)[0] == A


def test_room_holds_one_account_per_site():
    main = Account("x.com", "主号", A.card_id)
    cfg = Config(accounts=[main, Account("bilibili.com", "大会员", A.card_id)])
    assert room_conflict(cfg, A.card_id, "x.com") == main
    assert room_conflict(cfg, A.card_id, "playstation.com") is None
    assert room_conflict(cfg, B.card_id, "x.com") is None
    assert room_conflict(cfg, A.card_id, "x.com", ignore=main) is None  # moving/renaming the account itself


def test_accounts_in_missing_profiles_are_ignored():
    cfg = Config(accounts=[Account("x.com", "旧号", "chrome:Profile 9")], rules=[Rule("x.com", A.card_id)])
    assert decide("https://x.com", cfg, PROFILES)[0] == A
