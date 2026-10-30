import ast
import re
import string
import tkinter as tk
from pathlib import Path

import pytest

from profile_router import app, browsers, i18n, icons, shortcuts
from profile_router.config import Account, Config, Rule
from profile_router.i18n import t
from profile_router.translations import CATALOG

PKG = Path(app.__file__).parent
SOURCES = ["app.py", "browsers.py", "shortcuts.py"]
# CJK ideographs, kana, CJK punctuation (、「」) and full-width forms (（）：，)
CJK = re.compile(r"[　-〿぀-ヿ㐀-䶿一-鿿＀-￯]")
# Literals in app.py that may stay outside t():
#   "＋" is the icon-like "add" button on each site row; it is a symbol, the same in every language.
#   LAUNCH_LABELS values are source strings translated where shown: t(LAUNCH_LABELS[key]).
ALLOWED = {"＋", *app.LAUNCH_LABELS.values()}


def _tree(name: str) -> ast.AST:
    return ast.parse((PKG / name).read_text(encoding="utf-8"))


def _t_calls(tree: ast.AST):
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "t" and n.args:
            yield n


def used_keys() -> set[str]:
    keys = set(shortcuts.LOCATIONS.values()) | set(app.LAUNCH_LABELS.values())  # translated where shown
    for name in SOURCES:
        keys |= {c.args[0].value for c in _t_calls(_tree(name))
                 if isinstance(c.args[0], ast.Constant) and isinstance(c.args[0].value, str)}
    return keys


def fields(text: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(text) if f is not None}


def test_every_ui_string_has_japanese_and_english():
    missing = [k for k in used_keys() if not {"ja", "en"} <= set(CATALOG.get(k, {}))]
    assert not missing
    assert not set(CATALOG) - used_keys(), "unused catalog entries"


def test_placeholders_match_in_all_languages():
    for key, tr in CATALOG.items():
        for lang in ("ja", "en"):
            assert fields(tr[lang]) == fields(key), (key, lang)


def test_t_calls_pass_the_placeholders_they_use():
    for name in SOURCES:
        for c in _t_calls(_tree(name)):
            if isinstance(c.args[0], ast.Constant):
                assert fields(c.args[0].value) == {k.arg for k in c.keywords}, (name, c.lineno)


def test_no_chinese_left_outside_t():
    tree = _tree("app.py")
    inside = {id(sub) for c in _t_calls(tree) for sub in ast.walk(c.args[0])}
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.ClassDef, ast.FunctionDef)) and n.body
            and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    left = [(n.lineno, n.value) for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and CJK.search(n.value)
            and id(n) not in inside and id(n) not in docs and n.value not in ALLOWED]
    assert not left


def test_switching_language():
    i18n.set_language("en")
    assert t("打开") == "Open"
    assert t("已打开房间「{room}」", room="A") == 'Opened room "A"'
    i18n.set_language("ja")
    assert t("设置") == "設定"
    i18n.set_language("zh")
    assert t("打开") == "打开"
    assert t("已打开房间「{room}」", room="A") == "已打开房间「A」"
    assert t("没有这个词") == "没有这个词"
    assert i18n.set_language("auto") in i18n.LANGUAGES


# --- smoke: every window builds in every language ----------------------------------------------------


@pytest.fixture
def launcher(tmp_path, monkeypatch, root):
    monkeypatch.setenv("PROFILE_ROUTER_CONFIG", str(tmp_path / "config.json"))
    exe = tmp_path / "chrome.exe"
    exe.write_text("")
    rooms = [browsers.Profile("t", "Chrome", exe, "chromium", d, n, user_data_dir=str(tmp_path / "ud"))
             for d, n in (("Default", "我"), ("Profile 1", "小号"))]
    rooms.append(browsers.Profile("ff", "Firefox", exe, "firefox", "work", "work"))
    spec = browsers.BrowserSpec("t", "Chrome", "chromium", (exe,), tmp_path / "ud")
    manager = next(iter(browsers.PASSWORD_MANAGERS.values()))
    exts = [browsers.Extension(manager, "Bitwarden", "https://store/1", False),
            browsers.Extension("abc", "uBlock", "https://store/2", True)]
    monkeypatch.setattr(browsers, "all_profiles", lambda extras=(): rooms)
    monkeypatch.setattr(browsers, "installed_chromium", lambda: [spec])
    monkeypatch.setattr(browsers, "list_extensions", lambda p: exts)
    monkeypatch.setattr(browsers, "launch", lambda p, *urls, extra=(): None)
    monkeypatch.setattr(icons, "fetch_icon", lambda *a, **k: None)
    small = Account("x.com", "小号", "t:Profile 1", pages=["https://x.com/home"])
    Config(accounts=[Account("x.com", "主号", "t:Default"), small], sites=["github.com"],
           rules=[Rule("gist.github.com", "gone:x")], hidden_rooms=["ff:work"]).save()
    return app.LauncherApp(root)


@pytest.mark.parametrize("lang", ["zh", "ja", "en"])
def test_every_window_builds(lang, launcher, root):
    i18n.set_language(lang)
    launcher.rebuild()
    cfg, rooms = launcher.cfg, launcher.rooms
    a = cfg.accounts[1]
    launcher.show_hidden = True
    launcher.page.set("rooms")
    launcher.render()
    launcher.page.set("accounts")
    launcher.search.set("nothing-matches")
    launcher.search.set("")
    launcher._account_menu(a)
    launcher.switch(a)
    assert launcher.status.cget("text")
    wins = [
        app.AddAccountDialog(root, cfg, rooms, "x.com", on_done=lambda *x: None).win,
        app.NewRoomDialog(root, cfg, rooms, on_done=lambda *x: None).win,
        app.CopyExtensionsDialog(root, cfg, rooms, rooms[0]).win,
        app.PagesDialog(root, a, on_saved=lambda new: None).win,
        app.ShortcutDialog(root, launcher, a).win,
        app.ShortcutDialog(root, launcher, rooms[0]).win,
        app.RoomDialog(root, launcher, rooms[1]).win,
        app.DeleteAccountsDialog(root, cfg, launcher.profiles, [a], on_done=lambda x: None).win,
        app.DeleteAccountsDialog(root, cfg, launcher.profiles, cfg.accounts, on_done=lambda x: None,
                                 remove_site="x.com").win,
        app.SettingsDialog(root, cfg, rooms, on_saved=lambda: None).win,
        app.RulesDialog(root, cfg, rooms, on_saved=lambda: None).win,
    ]
    _, choices, remember = app.decide("https://x.com/", cfg, rooms)
    app.Picker(tk.Toplevel(root), "https://x.com/", cfg, choices, remember)
    _, choices, remember = app.decide("https://example.com/", cfg, rooms)
    app.Picker(tk.Toplevel(root), "https://example.com/", cfg, choices, remember)
    for w in wins:
        assert w.title()
        w.destroy()


def test_changing_language_in_settings_rebuilds_the_window(launcher, root):
    assert root.title() == "浏览器账号切换"
    d = app.SettingsDialog(root, launcher.cfg, launcher.rooms, on_saved=launcher.refresh,
                           on_language=launcher.rebuild)
    d.language.set("English")
    d.save()
    assert Config.load().language == "en" and i18n.current() == "en"
    assert root.title() == "Browser Account Switcher"
    assert "Accounts:" in launcher.status.cget("text")
