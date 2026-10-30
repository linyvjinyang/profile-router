"""Windows shortcuts (.lnk) that open an account or a room directly in the browser (no need for this app),
on the desktop or in the Start menu. (Windows does not let programs pin to the taskbar, so we don't offer it.)
"""

from __future__ import annotations

import os
import re
import struct
import subprocess
import uuid
from pathlib import Path

from .browsers import Profile, command
from .i18n import t
from .icons import PNG_SIG, icon_path

LOCATIONS = {"desktop": "桌面", "start": "开始菜单"}  # display names: Chinese source strings, pass through t()

# Values are passed through environment variables so no quoting can break the script.
_PS = r"""
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$folder = switch ($env:PR_WHERE) {
  'desktop' { [Environment]::GetFolderPath('Desktop') }
  'start'   { Join-Path ([Environment]::GetFolderPath('Programs')) 'Profile Router' }
  default   { $env:PR_WHERE }
}
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$path = Join-Path $folder ($env:PR_NAME + '.lnk')
$s = (New-Object -ComObject WScript.Shell).CreateShortcut($path)
$s.TargetPath = $env:PR_TARGET
$s.Arguments = $env:PR_ARGS
$s.WorkingDirectory = Split-Path $env:PR_TARGET
$s.Description = $env:PR_DESC
if ($env:PR_ICON) { $s.IconLocation = $env:PR_ICON + ',0' }
$s.Save()
Write-Output $path
"""


def png_to_ico(png: bytes) -> bytes:
    """An .ico holding one PNG image (supported by Windows since Vista)."""
    if not png.startswith(PNG_SIG):
        raise ValueError("not a PNG")
    w, h = struct.unpack(">II", png[16:24])
    entry = struct.pack("<BBBBHHII", w % 256, h % 256, 0, 0, 1, 32, len(png), 6 + 16)
    return struct.pack("<HHH", 0, 1, 1) + entry + png


def site_ico(site: str) -> Path | None:
    """The site's icon as .ico next to its PNG (shortcuts cannot use PNG icons)."""
    png = icon_path(site)
    if not png.is_file():
        return None
    ico = png.with_suffix(".ico")
    if not ico.is_file() or ico.stat().st_mtime < png.stat().st_mtime:
        ico.write_bytes(png_to_ico(png.read_bytes()))
    return ico


def safe_name(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip(" .") or t("快捷方式")


def _quote(arg: str) -> str:
    return f'"{arg}"' if (" " in arg or not arg) else arg


def create(name: str, p: Profile, urls: list[str], where: str, icon: Path | None = None,
           description: str = "") -> Path:
    """Create `name`.lnk on the "desktop", in the "start" menu, or in a folder path."""
    cmd = command(p, *urls)
    # WScript saves file names through the ANSI code page, which drops characters like "·"; save under an
    # ASCII name and rename in Python.
    temp = f"profile-router-{uuid.uuid4().hex[:8]}"
    env = dict(os.environ, PR_WHERE=where, PR_NAME=temp,
               PR_TARGET=cmd[0], PR_ARGS=" ".join(_quote(a) for a in cmd[1:]), PR_DESC=description,
               PR_ICON=str(icon) if icon else "")
    out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS], env=env,
                         capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    if out.returncode != 0 or not out.stdout.strip():
        raise OSError(out.stderr.strip() or t("创建快捷方式失败"))
    made = Path(out.stdout.strip().splitlines()[-1])
    final = made.with_name(safe_name(name) + ".lnk")
    os.replace(made, final)
    return final
