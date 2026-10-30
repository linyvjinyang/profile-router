import json
from pathlib import Path

from profile_router import browsers
from profile_router.browsers import BrowserSpec


def test_create_local_profile_seeds_name_and_skips_intro(tmp_path, monkeypatch):
    exe = tmp_path / "chrome.exe"
    exe.write_text("")
    data = tmp_path / "User Data"
    data.mkdir()
    (data / "Local State").write_text(json.dumps({"profile": {"info_cache": {"Default": {"name": "主"}}}}), "utf-8")
    (data / "Profile 1").mkdir()  # left over from a deleted profile: must not be reused
    spec = BrowserSpec("chrome", "Chrome", "chromium", (exe,), data)
    launched = []
    monkeypatch.setattr(browsers.subprocess, "Popen", lambda cmd, **kw: launched.append(cmd))

    d = browsers.create_local_profile(spec, "X 小号", ("https://x.com/",))

    assert d == "Profile 2"
    prefs = json.loads((data / d / "Preferences").read_text("utf-8"))
    assert prefs["profile"] == {"name": "X 小号", "using_default_name": False}
    assert launched == [[str(exe), "--profile-directory=Profile 2", "--no-first-run", "https://x.com/"]]


def test_store_url():
    assert browsers.store_url(browsers.PASSWORD_MANAGERS["Bitwarden"]).startswith("https://chromewebstore.google.com/detail/")
