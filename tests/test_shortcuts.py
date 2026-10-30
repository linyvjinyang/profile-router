import os
import struct
import subprocess
from pathlib import Path

import pytest

from profile_router import icons, shortcuts
from profile_router.browsers import Profile


def test_png_to_ico_wraps_png():
    png = icons.encode_png(2, 1, b"\x00" + bytes(8))
    ico = shortcuts.png_to_ico(png)
    assert struct.unpack("<HHH", ico[:6]) == (0, 1, 1)
    assert ico[22:] == png
    assert icons.to_png(ico) == png  # our own ICO reader understands it


def test_safe_name():
    assert shortcuts.safe_name('X: 小号/<1>') == "X_ 小号__1_"
    assert shortcuts.safe_name("...") == "快捷方式"


@pytest.mark.skipif(os.name != "nt", reason="Windows shortcuts")
def test_create_shortcut_in_folder(tmp_path):
    p = Profile("chrome", "Chrome", Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"), "chromium",
                "Profile 2", "小号")
    icon = tmp_path / "x.ico"
    icon.write_bytes(shortcuts.png_to_ico(icons.encode_png(1, 1, b"\x00" + bytes(4))))

    lnk = shortcuts.create("X · 小号", p, ["https://x.com/", "https://x.com/home"], str(tmp_path), icon, "测试")

    assert lnk == tmp_path / "X · 小号.lnk" and lnk.is_file()
    plain = tmp_path / "plain.lnk"  # WScript can only open ANSI-safe names
    plain.write_bytes(lnk.read_bytes())
    read = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "[Console]::OutputEncoding=[Text.Encoding]::UTF8; $s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:L);"
         "$s.TargetPath; $s.Arguments; $s.IconLocation"],
        env=dict(os.environ, L=str(plain)), capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    assert read[0].lower().endswith("chrome.exe")
    assert read[1] == '"--profile-directory=Profile 2" https://x.com/ https://x.com/home'
    assert read[2].startswith(str(icon))
