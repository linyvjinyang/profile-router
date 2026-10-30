"""Register / unregister Profile Router as a browser for the current Windows user (HKCU only).

Registering only makes it selectable; the user still picks it as the default for http/https
in Windows Settings > Apps > Default apps.
"""

from __future__ import annotations

import sys
import winreg
from pathlib import Path

APP = "ProfileRouter"
PROGID = "ProfileRouterURL"
CLIENT_KEY = rf"Software\Clients\StartMenuInternet\{APP}"
CLASS_KEY = rf"Software\Classes\{PROGID}"


def launcher_command() -> str:
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")
    runner = pythonw if pythonw.exists() else exe
    script = Path(__file__).resolve().parent.parent / "run.pyw"
    return f'"{runner}" "{script}" "%1"'


def _set(path: str, values: dict[str, str]) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_WRITE) as k:
        for name, value in values.items():
            winreg.SetValueEx(k, name, 0, winreg.REG_SZ, value)


def register() -> None:
    full = launcher_command()
    _set(CLASS_KEY, {"": "Profile Router URL", "URL Protocol": ""})
    _set(rf"{CLASS_KEY}\shell\open\command", {"": full})
    _set(CLIENT_KEY, {"": "Profile Router"})
    _set(rf"{CLIENT_KEY}\Capabilities", {
        "ApplicationName": "Profile Router",
        "ApplicationDescription": "Opens each link in the right browser profile",
    })
    _set(rf"{CLIENT_KEY}\Capabilities\URLAssociations", {"http": PROGID, "https": PROGID})
    _set(rf"{CLIENT_KEY}\shell\open\command", {"": full})
    _set(r"Software\RegisteredApplications", {APP: rf"{CLIENT_KEY}\Capabilities"})


def _delete_tree(path: str) -> None:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_ALL_ACCESS) as k:
            while True:
                try:
                    child = winreg.EnumKey(k, 0)
                except OSError:
                    break
                _delete_tree(rf"{path}\{child}")
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass


def unregister() -> None:
    _delete_tree(CLIENT_KEY)
    _delete_tree(CLASS_KEY)
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\RegisteredApplications", 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, APP)
    except FileNotFoundError:
        pass


def is_registered() -> bool:
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLIENT_KEY).Close()
        return True
    except FileNotFoundError:
        return False
