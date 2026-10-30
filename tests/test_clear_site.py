import json
import sqlite3
from pathlib import Path

from profile_router import browsers
from profile_router.browsers import Profile


def make_profile(root: Path) -> Profile:
    prof = root / "Profile 2"
    (prof / "Network").mkdir(parents=True)
    con = sqlite3.connect(prof / "Network" / "Cookies")
    con.execute("CREATE TABLE cookies (host_key TEXT, name TEXT, encrypted_value BLOB)")
    con.executemany("INSERT INTO cookies VALUES (?, ?, ?)", [
        (".x.com", "auth_token", b"secret"), ("x.com", "ct0", b"s"), ("api.x.com", "a", b"s"),
        (".notx.com", "keep", b"s"), (".bilibili.com", "SESSDATA", b"s")])
    con.commit()
    con.close()
    for name in ("https_x.com_0.indexeddb.leveldb", "https_mobile.x.com_0.indexeddb.blob",
                 "https_bilibili.com_0.indexeddb.leveldb"):
        (prof / "IndexedDB" / name).mkdir(parents=True)
    prefs = {"profile": {"content_settings": {"exceptions": {
        "notifications": {"https://x.com:443,*": {"setting": 1}, "https://bilibili.com:443,*": {"setting": 1}},
        "cookies": {"[*.]x.com,*": {"setting": 1}}}}}, "other": 1}
    (prof / "Preferences").write_text(json.dumps(prefs), "utf-8")
    return Profile("chrome", "Chrome", Path("chrome.exe"), "chromium", "Profile 2", "小号", user_data_dir=str(root))


def test_clear_site_data_only_touches_that_site(tmp_path):
    p = make_profile(tmp_path)

    done = browsers.clear_site_data(p, "x.com")

    assert done == {"cookies": 3, "storage": 2, "permissions": 2}
    con = sqlite3.connect(tmp_path / "Profile 2" / "Network" / "Cookies")
    left = sorted(h for (h,) in con.execute("SELECT host_key FROM cookies"))
    con.close()
    assert left == [".bilibili.com", ".notx.com"]
    assert [d.name for d in (tmp_path / "Profile 2" / "IndexedDB").iterdir()] == ["https_bilibili.com_0.indexeddb.leveldb"]
    prefs = json.loads((tmp_path / "Profile 2" / "Preferences").read_text("utf-8"))
    ex = prefs["profile"]["content_settings"]["exceptions"]
    assert list(ex["notifications"]) == ["https://bilibili.com:443,*"] and ex["cookies"] == {}
    assert prefs["other"] == 1


def test_site_settings_url():
    chrome = Profile("chrome", "Chrome", Path("c.exe"), "chromium", "Default", "x")
    edge = Profile("edge", "Edge", Path("e.exe"), "chromium", "Default", "x")
    assert browsers.site_settings_url(chrome, "x.com") == "chrome://settings/content/siteDetails?site=https://x.com"
    assert browsers.site_settings_url(edge, "x.com").startswith("edge://settings/content/siteDetails")
