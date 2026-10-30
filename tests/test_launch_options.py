from pathlib import Path

from profile_router import app, browsers
from profile_router.browsers import Profile, command, launch_args
from profile_router.config import Card, Config


def test_launch_args_from_options_and_custom():
    assert launch_args(["no_default_check", "mute", "unknown"], '--lang=ja "--user-agent=a b"') == [
        "--no-default-browser-check", "--mute-audio", "--lang=ja", "--user-agent=a b"]
    assert launch_args([], "") == []


def test_switches_go_before_the_urls():
    p = Profile("chrome", "Chrome", Path("chrome.exe"), "chromium", "Profile 2", "x")
    assert command(p, "https://a", extra=["--mute-audio"]) == [
        "chrome.exe", "--profile-directory=Profile 2", "--mute-audio", "https://a"]


def test_room_args_come_from_room_settings():
    p = Profile("chrome", "Chrome", Path("chrome.exe"), "chromium", "Profile 2", "x")
    cfg = Config(cards={p.card_id: Card(launch_options=["hide_restore"], launch_custom="--start-fullscreen")})
    assert app.room_args(cfg, p) == ["--hide-crash-restore-bubble", "--start-fullscreen"]
    assert app.room_args(Config(), p) == []


def test_switch_detection_in_binaries(tmp_path):
    exe = tmp_path / "chrome.exe"
    exe.write_bytes(b"MZ\x00")
    dll = tmp_path / "156.0.1.2" / "chrome.dll"
    dll.parent.mkdir()
    # a real switch, one only present as the tail of a longer name, and a feature name
    dll.write_bytes(b"\x00\x05no-default-browser-check\x00xx-mute-audio\x00WebContentsForceDark\x00")
    assert browsers.browser_version(exe) == "156.0.1.2"
    assert browsers.supports_switch(exe, "no-default-browser-check")
    assert not browsers.supports_switch(exe, "mute-audio")
    assert browsers.supports_switch(exe, "WebContentsForceDark")
    opts = browsers.available_options(exe)
    assert opts["no_default_check"] and opts["force_dark"] and not opts["mute"]
