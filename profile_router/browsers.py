"""Detect installed browsers and their user profiles, and launch a profile with a URL."""

from __future__ import annotations

import configparser
import json
import os
import re
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .i18n import t

LOCAL = Path(os.environ.get("LOCALAPPDATA", ""))
ROAMING = Path(os.environ.get("APPDATA", ""))
PF = Path(os.environ.get("ProgramFiles", r"C:\Program Files"))
PF86 = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))


@dataclass(frozen=True)
class BrowserSpec:
    key: str
    label: str
    kind: str  # "chromium" or "firefox"
    exes: tuple[Path, ...]
    data: Path  # Chromium "User Data" dir, or Firefox dir holding profiles.ini


SPECS = (
    BrowserSpec("chrome", "Chrome", "chromium",
                (PF / r"Google\Chrome\Application\chrome.exe", PF86 / r"Google\Chrome\Application\chrome.exe",
                 LOCAL / r"Google\Chrome\Application\chrome.exe"),
                LOCAL / r"Google\Chrome\User Data"),
    BrowserSpec("edge", "Edge", "chromium",
                (PF86 / r"Microsoft\Edge\Application\msedge.exe", PF / r"Microsoft\Edge\Application\msedge.exe"),
                LOCAL / r"Microsoft\Edge\User Data"),
    BrowserSpec("brave", "Brave", "chromium",
                (PF / r"BraveSoftware\Brave-Browser\Application\brave.exe",
                 LOCAL / r"BraveSoftware\Brave-Browser\Application\brave.exe"),
                LOCAL / r"BraveSoftware\Brave-Browser\User Data"),
    BrowserSpec("vivaldi", "Vivaldi", "chromium",
                (LOCAL / r"Vivaldi\Application\vivaldi.exe", PF / r"Vivaldi\Application\vivaldi.exe"),
                LOCAL / r"Vivaldi\User Data"),
    BrowserSpec("iron", "Iron", "chromium",
                (PF / r"SRWare Iron (64-Bit)\chrome.exe", PF86 / r"SRWare Iron\chrome.exe"),
                LOCAL / r"Chromium\User Data"),
    BrowserSpec("firefox", "Firefox", "firefox",
                (PF / r"Mozilla Firefox\firefox.exe", PF86 / r"Mozilla Firefox\firefox.exe"),
                ROAMING / r"Mozilla\Firefox"),
)


@dataclass(frozen=True)
class Profile:
    browser: str  # BrowserSpec.key
    browser_label: str
    exe: Path
    kind: str
    profile_id: str  # Chromium profile directory ("Default", "Profile 1"), or Firefox profile name
    name: str  # display name the browser shows
    account: str = ""  # signed-in account, if any
    user_data_dir: str = ""  # only for profiles outside the browser's default data dir

    @property
    def card_id(self) -> str:
        return f"{self.browser}:{self.profile_id}"


def _first_existing(paths: tuple[Path, ...]) -> Path | None:
    return next((p for p in paths if p.is_file()), None)


def chromium_profiles(local_state: Path) -> list[tuple[str, str, str]]:
    """(profile dir, display name, account) from a Chromium "Local State" file, in browser order."""
    try:
        state = json.loads(local_state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    info = state.get("profile", {}).get("info_cache", {})
    order = state.get("profile", {}).get("profiles_order") or sorted(info, key=_profile_sort_key)
    return [(d, info[d].get("name") or d, info[d].get("user_name") or "") for d in order if d in info]


def _profile_sort_key(d: str) -> tuple[int, int]:
    if d == "Default":
        return (0, 0)
    tail = d.rsplit(" ", 1)[-1]
    return (1, int(tail) if tail.isdigit() else 0)


def firefox_profiles(profiles_ini: Path) -> list[str]:
    cp = configparser.ConfigParser()
    try:
        cp.read(profiles_ini, encoding="utf-8")
    except (OSError, configparser.Error):
        return []
    return [cp[s]["Name"] for s in cp.sections() if s.startswith("Profile") and "Name" in cp[s]]


def detect() -> list[Profile]:
    found: list[Profile] = []
    for spec in SPECS:
        exe = _first_existing(spec.exes)
        if not exe:
            continue
        if spec.kind == "chromium":
            for d, name, account in chromium_profiles(spec.data / "Local State"):
                found.append(Profile(spec.key, spec.label, exe, spec.kind, d, name, account))
        else:
            for name in firefox_profiles(spec.data / "profiles.ini"):
                found.append(Profile(spec.key, spec.label, exe, spec.kind, name, name))
    return found


def all_profiles(extras=()) -> list[Profile]:
    """Detected profiles plus configured ones outside the default data dirs (config.ExtraProfile)."""
    return detect() + [Profile(e.browser, e.browser_label, Path(e.exe), "chromium", e.profile_id, e.name,
                               user_data_dir=e.user_data_dir) for e in extras]


def watched_files(extras=()) -> list[Path]:
    """Files whose change means the list of profiles (or their names) changed."""
    files = [s.data / ("Local State" if s.kind == "chromium" else "profiles.ini") for s in SPECS]
    files += [Path(e.user_data_dir) / "Local State" for e in extras]
    return list(dict.fromkeys(files))


def signature(files: list[Path]) -> tuple:
    """Cheap change detector: modification time and size of each file (None when missing)."""
    out = []
    for f in files:
        try:
            st = f.stat()
            out.append((st.st_mtime_ns, st.st_size))
        except OSError:
            out.append(None)
    return tuple(out)


def installed_chromium() -> list[BrowserSpec]:
    return [s for s in SPECS if s.kind == "chromium" and _first_existing(s.exes)]


def next_profile_dir(spec: BrowserSpec) -> str:
    """A Chromium profile directory name not used yet; launching it makes the browser create it."""
    used = {d for d, _, _ in chromium_profiles(spec.data / "Local State")}
    n = 1
    while f"Profile {n}" in used or (spec.data / f"Profile {n}").exists():
        n += 1
    return f"Profile {n}"


def command(p: Profile, *urls: str | None, extra: list[str] | tuple = ()) -> list[str]:
    """Command line opening profile `p`, with each URL in its own tab; `extra` are launch switches."""
    urls = tuple(u for u in urls if u)
    if p.kind == "chromium":
        cmd = [str(p.exe)]
        if p.user_data_dir:
            cmd.append(f"--user-data-dir={p.user_data_dir}")
        return cmd + [f"--profile-directory={p.profile_id}", *extra, *urls]
    cmd = [str(p.exe), "-P", p.profile_id, *extra]
    for u in urls:
        cmd += ["-new-tab", u]
    return cmd


def launch(p: Profile, *urls: str | None, extra: list[str] | tuple = ()) -> None:
    subprocess.Popen(command(p, *urls, extra=extra), close_fds=True)


# Launch switches offered per room: key -> (switches, the name to look for in the browser's binaries).
# Only switches known to still work in current Chromium; each is shown only if this browser version has it.
LAUNCH_OPTIONS = {
    "no_default_check": (("--no-default-browser-check",), "no-default-browser-check"),
    "hide_restore": (("--hide-crash-restore-bubble",), "hide-crash-restore-bubble"),
    "no_first_run": (("--no-first-run",), "no-first-run"),
    "no_search_choice": (("--disable-search-engine-choice-screen",), "disable-search-engine-choice-screen"),
    "maximized": (("--start-maximized",), "start-maximized"),
    "mute": (("--mute-audio",), "mute-audio"),
    "force_dark": (("--enable-features=WebContentsForceDark",), "WebContentsForceDark"),
}

def browser_binaries(exe: Path) -> list[Path]:
    """The browser's main executable and its core DLL (in the newest version folder, or next to the exe)."""
    found = [exe]
    for name in ("chrome.dll", "msedge.dll", "vivaldi.dll"):
        found += sorted(exe.parent.glob(f"*/{name}"), key=lambda p: [int(x) if x.isdigit() else 0
                                                                     for x in p.parent.name.split(".")])[-1:]
        found += [exe.parent / name] if (exe.parent / name).is_file() else []
    return [p for p in found if p.is_file()]


def browser_version(exe: Path) -> str:
    for dll in browser_binaries(exe)[1:]:
        if re.fullmatch(r"\d+(\.\d+){3}", dll.parent.name):
            return dll.parent.name
    manifest = sorted(exe.parent.glob("*.manifest"), key=lambda p: p.stat().st_mtime)
    m = re.match(r"(\d+(?:\.\d+){3})", manifest[-1].name) if manifest else None
    return m.group(1) if m else ""


def supports_switch(exe: Path, name: str) -> bool:
    """Whether this browser version still contains the switch/feature name (switches removed from Chromium
    disappear from its binaries). A name preceded by a letter, digit or dash is a different, longer string."""
    import mmap

    needle = name.encode() + b"\x00"
    word = frozenset(b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    for binary in browser_binaries(exe):
        try:
            with open(binary, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
                i = m.find(needle)
                while i != -1:
                    if i == 0 or m[i - 1] not in word:
                        return True
                    i = m.find(needle, i + 1)
        except (OSError, ValueError):
            continue
    return False


def available_options(exe: Path) -> dict[str, bool]:
    """LAUNCH_OPTIONS keys -> supported by this browser version (cached per executable and its mtime)."""
    key = (str(exe), exe.stat().st_mtime if exe.exists() else 0)
    if key not in _options_cache:
        _options_cache[key] = {k: supports_switch(exe, probe) for k, (_, probe) in LAUNCH_OPTIONS.items()}
    return _options_cache[key]


_options_cache: dict[tuple[str, float], dict[str, bool]] = {}


def launch_args(options: list[str], custom: str) -> list[str]:
    """Switches for the chosen option keys plus the user's own (space separated, "quotes" keep spaces)."""
    args = [s for k in options if k in LAUNCH_OPTIONS for s in LAUNCH_OPTIONS[k][0]]
    return args + [a.strip('"') for a in re.findall(r'"[^"]*"|\S+', custom or "")]


@dataclass(frozen=True)
class Extension:
    id: str
    name: str
    url: str  # store page to install it from
    enabled: bool


# Chromium install locations worth offering: store installs and external installs that came from the store.
# Excluded: unpacked (4), component (5, 10), command line (8), policy (7, 9).
_OFFERABLE_LOCATIONS = {1, 2, 3, 6}
_LOCALE_ORDER = ("zh_CN", "zh_TW", "ja", "en", "en_US")


def profile_path(p: Profile) -> Path | None:
    if p.kind != "chromium":
        return None
    if p.user_data_dir:
        return Path(p.user_data_dir) / p.profile_id
    spec = next((s for s in SPECS if s.key == p.browser), None)
    return spec.data / p.profile_id if spec else None


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}


def _extension_name(version_dir: Path, manifest: dict) -> str:
    name = manifest.get("name", "")
    if not name.startswith("__MSG_"):
        return name
    key = name[6:-2].lower()
    locales = [*_LOCALE_ORDER, manifest.get("default_locale", "")]
    for loc in filter(None, locales):
        messages = {k.lower(): v for k, v in _read_json(version_dir / "_locales" / loc / "messages.json").items()}
        if key in messages and isinstance(messages[key], dict):
            return messages[key].get("message", name)
    return name


def list_extensions(p: Profile) -> list[Extension]:
    """Extensions installed in a Chromium profile that can be reinstalled from a store, sorted by name."""
    path = profile_path(p)
    if not path or not (path / "Extensions").is_dir():
        return []
    settings: dict = {}
    for f in ("Preferences", "Secure Preferences"):
        settings.update(_read_json(path / f).get("extensions", {}).get("settings", {}))
    found = []
    for ext_dir in (path / "Extensions").iterdir():
        s = settings.get(ext_dir.name, {})
        if s.get("location") not in _OFFERABLE_LOCATIONS:
            continue
        versions = sorted(v for v in ext_dir.iterdir() if (v / "manifest.json").is_file())
        if not versions:
            continue
        manifest = _read_json(versions[-1] / "manifest.json")
        if s.get("from_webstore"):
            url = store_url(ext_dir.name)
        elif p.browser == "edge":
            url = f"https://microsoftedge.microsoft.com/addons/detail/{ext_dir.name}"
        else:
            continue
        found.append(Extension(ext_dir.name, _extension_name(versions[-1], manifest) or ext_dir.name, url,
                               not s.get("disable_reasons")))
    return sorted(found, key=lambda e: e.name.lower())


def is_running(exe: Path) -> bool:
    """Whether any process runs from this exact executable (Iron and Chrome both use chrome.exe)."""
    import ctypes
    from ctypes import wintypes

    psapi, kernel32 = ctypes.WinDLL("psapi"), ctypes.WinDLL("kernel32")
    pids = (wintypes.DWORD * 4096)()
    got = wintypes.DWORD()
    if not psapi.EnumProcesses(pids, ctypes.sizeof(pids), ctypes.byref(got)):
        return False
    target = str(exe).lower()
    buf = ctypes.create_unicode_buffer(1024)
    for pid in pids[: got.value // ctypes.sizeof(wintypes.DWORD)]:
        h = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            continue
        size = wintypes.DWORD(len(buf))
        try:
            if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) and buf.value.lower() == target:
                return True
        finally:
            kernel32.CloseHandle(h)
    return False


def to_recycle_bin(path: Path) -> bool:
    """Move a folder to the Windows Recycle Bin (recoverable), without prompts."""
    import ctypes
    from ctypes import wintypes

    class SHFILEOPSTRUCTW(ctypes.Structure):
        _fields_ = [("hwnd", wintypes.HWND), ("wFunc", wintypes.UINT), ("pFrom", wintypes.LPCWSTR),
                    ("pTo", wintypes.LPCWSTR), ("fFlags", ctypes.c_ushort), ("fAnyOperationsAborted", wintypes.BOOL),
                    ("hNameMappings", ctypes.c_void_p), ("lpszProgressTitle", wintypes.LPCWSTR)]

    FO_DELETE, FOF_SILENT, FOF_NOCONFIRMATION, FOF_ALLOWUNDO, FOF_NOERRORUI = 3, 0x4, 0x10, 0x40, 0x400
    op = SHFILEOPSTRUCTW(wFunc=FO_DELETE, pFrom=str(path) + "\0\0",
                         fFlags=FOF_SILENT | FOF_NOCONFIRMATION | FOF_ALLOWUNDO | FOF_NOERRORUI)
    return ctypes.windll.shell32.SHFileOperationW(ctypes.byref(op)) == 0 and not op.fAnyOperationsAborted


def data_dir(p: Profile) -> Path | None:
    """The browser's "User Data" folder holding this profile."""
    path = profile_path(p)
    return path.parent if path else None


def forget_profile(local_state: Path, profile_id: str) -> None:
    """Remove a deleted profile from the browser's profile list so it does not show up any more."""
    state = _read_json(local_state)
    prof = state.get("profile", {})
    prof.get("info_cache", {}).pop(profile_id, None)
    for key in ("profiles_order", "last_active_profiles"):
        if isinstance(prof.get(key), list):
            prof[key] = [d for d in prof[key] if d != profile_id]
    if prof.get("last_used") == profile_id:
        prof["last_used"] = "Default"
    tmp = local_state.with_suffix(".profile-router.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    tmp.replace(local_state)


def delete_profile(p: Profile) -> None:
    """Move a Chromium profile folder to the Recycle Bin and drop it from the browser's list.
    The browser must be closed (callers check is_running first)."""
    path, root = profile_path(p), data_dir(p)
    if not path or not root or p.kind != "chromium":
        raise ValueError(t("只能删除 Chromium 系浏览器的用户"))
    if path.exists() and not to_recycle_bin(path):
        raise OSError(t("没能把 {path} 移到回收站", path=path))
    forget_profile(root / "Local State", p.profile_id)


def _host_matches(host: str, site: str) -> bool:
    host, site = host.lower().lstrip("."), site.lower().strip("*.")
    return host == site or host.endswith("." + site)


def _origin_host(key: str) -> str:
    """Host from a content-settings pattern such as "https://x.com:443,*" or "[*.]x.com,*"."""
    first = key.split(",")[0]
    first = re.sub(r"^[a-z-]+://", "", first).replace("[*.]", "")
    return first.split("/")[0].split(":")[0]


def site_settings_url(p: Profile, site: str) -> str:
    """The browser's own page for one site's data and permissions (it has a "delete data" button)."""
    scheme = "edge" if p.browser == "edge" else "chrome"
    return f"{scheme}://settings/content/siteDetails?site=https://{site.strip('*.')}"


def clear_site_data(p: Profile, site: str) -> dict[str, int]:
    """Log a room out of a site: delete that site's cookies, IndexedDB/storage folders and saved permissions
    in this profile. Values are never read. The browser must be closed (callers check is_running first)."""
    path = profile_path(p)
    if not path or p.kind != "chromium":
        raise ValueError(t("只能清除 Chromium 系浏览器的网站数据"))
    done = {"cookies": 0, "storage": 0, "permissions": 0}
    for db in (path / "Network" / "Cookies", path / "Cookies"):
        if db.is_file():
            con = sqlite3.connect(db)
            try:
                hosts = [h for (h,) in con.execute("SELECT DISTINCT host_key FROM cookies")]
                drop = [h for h in hosts if _host_matches(h, site)]
                for h in drop:
                    done["cookies"] += con.execute("DELETE FROM cookies WHERE host_key = ?", (h,)).rowcount
                con.commit()
            finally:
                con.close()
    for folder in ("IndexedDB", "File System", "Service Worker/CacheStorage"):
        base = path / folder
        if not base.is_dir():
            continue
        for item in base.iterdir():
            m = re.match(r"^https?_(.+?)_\d+", item.name)
            if m and _host_matches(m.group(1), site):
                shutil.rmtree(item, ignore_errors=True) if item.is_dir() else item.unlink(missing_ok=True)
                done["storage"] += 1
    prefs_file = path / "Preferences"
    prefs = _read_json(prefs_file)
    exceptions = prefs.get("profile", {}).get("content_settings", {}).get("exceptions", {})
    for setting in exceptions.values():
        if isinstance(setting, dict):
            for key in [k for k in setting if _host_matches(_origin_host(k), site)]:
                del setting[key]
                done["permissions"] += 1
    if done["permissions"]:
        tmp = prefs_file.with_suffix(".profile-router.tmp")
        tmp.write_text(json.dumps(prefs, ensure_ascii=False), encoding="utf-8")
        tmp.replace(prefs_file)
    return done


PASSWORD_MANAGERS = {  # Chrome Web Store ids; Edge installs these too after allowing other stores
    "LastPass": "hdokiejnpimakedhajhdlcegeplioahd",
    "Bitwarden": "nngceckbapebfimnlniiiahkandclblb",
    "1Password": "aeblfdkhhhdcdjpifhhbdiojplfjncoa",
    "KeePassXC": "oboonakemofpalcgghocfoadofidjkkk",
}


def store_url(extension_id: str) -> str:
    return f"https://chromewebstore.google.com/detail/{extension_id}"


def create_local_profile(spec: BrowserSpec, name: str, urls: tuple[str, ...] = ()) -> str:
    """Create a local (not signed-in) profile named `name` and open it, skipping the sign-in intro.

    The profile directory is pre-seeded with its display name; --no-first-run stops Chrome from opening
    chrome://intro for the new profile. Only a new, unused directory is written.
    """
    exe = _first_existing(spec.exes)
    if not exe:
        raise FileNotFoundError(spec.label)
    d = next_profile_dir(spec)
    seed_profile(spec.data / d, name)
    subprocess.Popen([str(exe), f"--profile-directory={d}", "--no-first-run", *urls], close_fds=True)
    return d


def seed_profile(path: Path, name: str) -> None:
    path.mkdir(parents=True)
    prefs = {"profile": {"name": name, "using_default_name": False}}
    (path / "Preferences").write_text(json.dumps(prefs, ensure_ascii=False), encoding="utf-8")
