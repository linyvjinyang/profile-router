import json
import os
import tkinter as tk

import pytest

from profile_router import app, browsers
from profile_router.config import Config, ExtraProfile


def write_state(data_dir, names: dict) -> None:
    info = {d: {"name": n} for d, n in names.items()}
    (data_dir / "Local State").write_text(json.dumps({"profile": {"info_cache": info}}), "utf-8")
    os.utime(data_dir / "Local State", ns=(0, os.stat(data_dir / "Local State").st_mtime_ns + 10**9))


def test_signature_notices_changes(tmp_path):
    f = tmp_path / "Local State"
    before = browsers.signature([f])
    assert before == (None,)
    write_state(tmp_path, {"Default": "主"})
    assert browsers.signature([f]) != before


def test_shortcut_dialog_prefills_the_launch_target(tmp_path, monkeypatch, root):
    from profile_router.config import Account
    monkeypatch.setenv("PROFILE_ROUTER_CONFIG", str(tmp_path / "config.json"))
    exe = tmp_path / "chrome.exe"
    exe.write_text("")
    rooms = [browsers.Profile("t", "测试", exe, "chromium", d, n) for d, n in (("Default", "我"), ("Profile 1", "小号"))]
    monkeypatch.setattr(browsers, "all_profiles", lambda extras=(): rooms)
    small = Account("x.com", "小号", "t:Profile 1", pages=["https://x.com/home"])
    Config(accounts=[Account("x.com", "主号", "t:Default"), small]).save()
    launcher = app.LauncherApp(root)

    d = app.ShortcutDialog(root, launcher, small)
    assert d.item.get() == "账号：x.com · 小号（房间「小号」）"
    assert d.name.get() == "x.com · 小号" and "https://x.com/home" in d.opens.cget("text")
    assert d.where["desktop"].get() and not d.where["start"].get() and "taskbar" not in d.where
    d.win.destroy()

    d = app.ShortcutDialog(root, launcher, rooms[0])
    assert d.item.get() == "房间：我（测试）" and d.opens.cget("text") == "只打开这个房间"
    d.win.destroy()


def test_new_browser_profile_shows_up_without_restart(tmp_path, monkeypatch, root):
    monkeypatch.setenv("PROFILE_ROUTER_CONFIG", str(tmp_path / "config.json"))
    data = tmp_path / "ud"
    data.mkdir()
    write_state(data, {"Default": "主"})
    exe = tmp_path / "chrome.exe"
    exe.write_text("")
    # Rooms come from this test data dir only: Local State lists the profiles.
    monkeypatch.setattr(browsers, "detect", lambda: [])
    monkeypatch.setattr(browsers, "all_profiles", lambda extras=(): [
        browsers.Profile("t", "测试", exe, "chromium", d, v["name"], user_data_dir=str(data))
        for d, v in json.loads((data / "Local State").read_text("utf-8"))["profile"]["info_cache"].items()])
    Config(extra_profiles=[ExtraProfile("t", "测试", str(exe), str(data), "Default", "主")]).save()

    launcher = app.LauncherApp(root)
    assert [p.name for p in launcher.profiles] == ["主"]

    write_state(data, {"Default": "主", "Profile 1": "小号"})  # the user adds a profile in the browser
    launcher._poll()
    assert [p.name for p in launcher.profiles] == ["主", "小号"]
    assert "新房间 小号" in launcher.status.cget("text")
