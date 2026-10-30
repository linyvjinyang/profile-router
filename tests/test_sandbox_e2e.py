"""End to end: log two sandbox Chrome profiles into the fake site as different accounts, then check that
opening the site with each profile's launch arguments shows that profile's own account.

Uses headless Chrome and a throwaway --user-data-dir, so real browser profiles are untouched.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from fake_site import serve  # noqa: E402

from profile_router.browsers import SPECS, Profile, command  # noqa: E402

CHROME = next((p for s in SPECS if s.key == "chrome" for p in s.exes if p.is_file()), None)
HEADLESS = ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
            "--disable-extensions", "--virtual-time-budget=3000", "--dump-dom"]


def dump(p: Profile, url: str) -> str:
    cmd = command(p)
    return subprocess.run(cmd + HEADLESS + [url], capture_output=True, text=True, encoding="utf-8",
                          timeout=60).stdout


def account_on_page(dom: str) -> str:
    m = re.search(r'id="account"[^>]*>([^<]*)<', dom)
    return m.group(1) if m else ""


@pytest.mark.skipif(CHROME is None, reason="Chrome not installed")
def test_each_profile_keeps_its_own_login(tmp_path):
    server = serve(port=0, background=True)
    port = server.server_address[1]
    try:
        users = {"Profile 1": "主号", "Profile 2": "小号"}
        profiles = {d: Profile("test", "Chrome", CHROME, "chromium", d, d, user_data_dir=str(tmp_path / "ud"))
                    for d in users}
        for d, name in users.items():
            assert account_on_page(dump(profiles[d], f"http://x.localhost:{port}/login?as={name}")) == name
        for d, name in users.items():
            assert account_on_page(dump(profiles[d], f"http://x.localhost:{port}/")) == name
    finally:
        server.shutdown()
