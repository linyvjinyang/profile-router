import json

from profile_router.browsers import Profile, chromium_profiles, command
from profile_router.config import Config, Rule
from profile_router.router import host_of, matches, normalize, route


def test_host_suffix_and_glob():
    assert matches("github.com", "github.com")
    assert matches("github.com", "gist.github.com")
    assert not matches("github.com", "notgithub.com")
    assert matches("*.mbga.jp", "game.mbga.jp")
    assert not matches("", "github.com")


def test_most_specific_rule_wins():
    rules = [Rule("google.com", "chrome:Default"), Rule("mail.google.com", "chrome:Profile 2")]
    assert route("https://mail.google.com/mail/u/0", rules) == "chrome:Profile 2"
    assert route("https://www.google.com/search?q=x", rules) == "chrome:Default"
    assert route("https://example.com", rules) is None


def test_normalize_and_host():
    assert normalize(" github.com ") == "https://github.com"
    assert normalize("about:blank") == "about:blank"
    assert host_of("GitHub.com/x") == "github.com"


def test_chromium_local_state(tmp_path):
    state = {"profile": {"info_cache": {
        "Profile 2": {"name": "小号", "user_name": "b@example.com"},
        "Default": {"name": "主号"},
    }}}
    f = tmp_path / "Local State"
    f.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    assert chromium_profiles(f) == [("Default", "主号", ""), ("Profile 2", "小号", "b@example.com")]
    assert chromium_profiles(tmp_path / "missing") == []


def test_commands():
    chrome = Profile("chrome", "Chrome", "chrome.exe", "chromium", "Profile 2", "小号")
    assert command(chrome, "https://a.b") == ["chrome.exe", "--profile-directory=Profile 2", "https://a.b"]
    ff = Profile("firefox", "Firefox", "firefox.exe", "firefox", "work", "work")
    assert command(ff, "https://a.b") == ["firefox.exe", "-P", "work", "-new-tab", "https://a.b"]
    assert command(ff) == ["firefox.exe", "-P", "work"]


def test_config_roundtrip(tmp_path):
    path = tmp_path / "c.json"
    cfg = Config()
    cfg.card("chrome:Default").name = "主号"
    cfg.rules.append(Rule("github.com", "chrome:Default"))
    cfg.save(path)
    back = Config.load(path)
    assert back.cards["chrome:Default"].name == "主号"
    assert back.rules == [Rule("github.com", "chrome:Default")]
    assert Config.load(tmp_path / "none.json").rules == []
