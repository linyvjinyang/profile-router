import json
from pathlib import Path

from profile_router.browsers import Profile, list_extensions


def make_ext(profile: Path, ext_id: str, manifest: dict, locales: dict | None = None) -> None:
    v = profile / "Extensions" / ext_id / "1.0_0"
    v.mkdir(parents=True)
    (v / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), "utf-8")
    for loc, messages in (locales or {}).items():
        (v / "_locales" / loc).mkdir(parents=True)
        (v / "_locales" / loc / "messages.json").write_text(json.dumps(messages, ensure_ascii=False), "utf-8")


def test_list_extensions_filters_and_names(tmp_path):
    prof = tmp_path / "Default"
    make_ext(prof, "aaa", {"name": "LastPass"})
    make_ext(prof, "bbb", {"name": "__MSG_extName__", "default_locale": "en"},
             {"en": {"extName": {"message": "Tampermonkey"}}, "zh_CN": {"extname": {"message": "篡改猴"}}})
    make_ext(prof, "ccc", {"name": "Payments"})  # component: not offered
    make_ext(prof, "ddd", {"name": "My dev build"})  # unpacked: not offered
    make_ext(prof, "eee", {"name": "Old"})  # disabled, still offered
    settings = {"aaa": {"location": 6, "from_webstore": True}, "bbb": {"location": 1, "from_webstore": True},
                "ccc": {"location": 10, "from_webstore": True}, "ddd": {"location": 4},
                "eee": {"location": 1, "from_webstore": True, "disable_reasons": [1]}}
    (prof / "Secure Preferences").write_text(json.dumps({"extensions": {"settings": settings}}), "utf-8")
    p = Profile("chrome", "Chrome", Path("chrome.exe"), "chromium", "Default", "主", user_data_dir=str(tmp_path))

    got = list_extensions(p)

    assert [(e.id, e.name, e.enabled) for e in got] == [("aaa", "LastPass", True), ("eee", "Old", False),
                                                        ("bbb", "篡改猴", True)]
    assert got[0].url == "https://chromewebstore.google.com/detail/aaa"


def test_list_extensions_missing_profile(tmp_path):
    p = Profile("chrome", "Chrome", Path("chrome.exe"), "chromium", "Nope", "x", user_data_dir=str(tmp_path))
    assert list_extensions(p) == []
