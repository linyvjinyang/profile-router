"""Try account switching without real accounts or touching your browsers' own profiles.

Starts the fake sites, sets up three test Chrome profiles in a separate sandbox folder, and opens the
launcher with a demo config (your real config in %APPDATA% is not used):

    python tools/demo.py

Then in the launcher: click an account (e.g. x.localhost · 小号). The first time, the fake site shows
"未登录"; click the matching name to log in. After that each profile stays logged in as its own account.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from fake_site import PORT, serve  # noqa: E402

from profile_router import browsers  # noqa: E402
from profile_router.config import Account, Card, Config, ExtraProfile  # noqa: E402

SANDBOX = ROOT / ".sandbox"
TEST_USERS = (("Profile 1", "测试用户 A", "#4F7BE8"), ("Profile 2", "测试用户 B", "#E8744F"),
              ("Profile 3", "测试用户 C", "#3BA776"))
ACCOUNTS = (("x.localhost", "主号", 0), ("x.localhost", "小号", 1), ("x.localhost", "工作号", 2),
            ("bili.localhost", "大会员", 0), ("bili.localhost", "追番号", 2),
            ("psn.localhost", "日服", 1), ("psn.localhost", "港服", 2))


def demo_config() -> Config:
    chrome = next((s for s in browsers.SPECS if s.key == "chrome"), None)
    exe = next((p for p in chrome.exes if p.is_file()), None) if chrome else None
    if not exe:
        raise SystemExit("需要 Chrome 才能跑演示。")
    cfg = Config(ask_unmatched=True)
    data_dir = str(SANDBOX / "chrome")
    for d, name, color in TEST_USERS:
        cfg.extra_profiles.append(ExtraProfile("test", "Chrome 测试", str(exe), data_dir, d, name))
        cfg.cards[f"test:{d}"] = Card(color=color)
    for site, label, i in ACCOUNTS:
        cfg.accounts.append(Account(site, label, f"test:{TEST_USERS[i][0]}", f"http://{site}:{PORT}/"))
    return cfg


def main() -> None:
    SANDBOX.mkdir(exist_ok=True)
    path = SANDBOX / "demo_config.json"
    if not path.exists():
        demo_config().save(path)
    os.environ["PROFILE_ROUTER_CONFIG"] = str(path)
    serve(background=True)
    from profile_router.app import run_launcher

    run_launcher()


if __name__ == "__main__":
    main()
