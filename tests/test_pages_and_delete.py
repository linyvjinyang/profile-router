import json
import sys
from pathlib import Path

from profile_router import browsers
from profile_router.app import delete_block_reason
from profile_router.browsers import Profile, command
from profile_router.config import Account, Card, Config, Rule
from profile_router.router import account_urls


def room(profile_id="Profile 3", account="", kind="chromium", data=""):
    return Profile("chrome", "Chrome", Path("chrome.exe"), kind, profile_id, "x", account, user_data_dir=data)


def test_account_opens_its_pages_or_its_start_page():
    assert account_urls(Account("x.com", "小号", "c")) == ["https://x.com/"]
    a = Account("bilibili.com", "大会员", "c", pages=["t.bilibili.com", "https://member.bilibili.com/", " "])
    assert account_urls(a) == ["https://t.bilibili.com", "https://member.bilibili.com/"]


def test_command_opens_every_page_in_its_own_tab():
    chrome = room("Profile 2")
    assert command(chrome, "https://a", "https://b") == ["chrome.exe", "--profile-directory=Profile 2", "https://a",
                                                        "https://b"]
    ff = Profile("firefox", "Firefox", Path("firefox.exe"), "firefox", "work", "work")
    assert command(ff, "https://a", "https://b") == ["firefox.exe", "-P", "work", "-new-tab", "https://a",
                                                    "-new-tab", "https://b"]


def test_main_and_used_rooms_cannot_be_deleted():
    cfg = Config(accounts=[Account("x.com", "小号", "chrome:Profile 2")])
    assert "主房间" in delete_block_reason(cfg, room("Default"))
    assert "浏览器账号" in delete_block_reason(cfg, room("Profile 4", account="me@example.com"))
    assert "1 个网站账号" in delete_block_reason(cfg, room("Profile 2"))
    assert "Chromium" in delete_block_reason(cfg, room("work", kind="firefox"))
    assert delete_block_reason(cfg, room("Profile 3")) is None


def test_delete_profile_moves_folder_and_forgets_it(tmp_path, monkeypatch):
    (tmp_path / "Profile 3").mkdir()
    state = {"profile": {"info_cache": {"Default": {"name": "主"}, "Profile 3": {"name": "旧"}},
                         "last_used": "Profile 3", "last_active_profiles": ["Default", "Profile 3"]},
             "other": {"kept": True}}
    (tmp_path / "Local State").write_text(json.dumps(state), "utf-8")
    trashed = []
    monkeypatch.setattr(browsers, "to_recycle_bin", lambda p: trashed.append(p) or True)

    browsers.delete_profile(room("Profile 3", data=str(tmp_path)))

    assert trashed == [tmp_path / "Profile 3"]
    after = json.loads((tmp_path / "Local State").read_text("utf-8"))
    assert list(after["profile"]["info_cache"]) == ["Default"]
    assert after["profile"]["last_used"] == "Default"
    assert after["profile"]["last_active_profiles"] == ["Default"]
    assert after["other"] == {"kept": True}


def test_forget_room_drops_its_registrations():
    cfg = Config(cards={"chrome:Profile 3": Card(name="旧")}, accounts=[Account("x.com", "a", "chrome:Profile 3"),
                                                                      Account("x.com", "b", "chrome:Default")],
                 rules=[Rule("a.com", "chrome:Profile 3")], hidden_rooms=["chrome:Profile 3"],
                 fallback="chrome:Profile 3")
    cfg.forget_room("chrome:Profile 3")
    assert cfg.cards == {} and [a.label for a in cfg.accounts] == ["b"]
    assert cfg.rules == [] and cfg.hidden_rooms == [] and cfg.fallback == ""


def test_is_running():
    assert browsers.is_running(Path(sys.executable))
    assert not browsers.is_running(Path(r"C:\nowhere\not-a-browser.exe"))
