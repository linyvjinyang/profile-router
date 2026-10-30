"""UI language: Simplified Chinese (the source strings), Japanese and English.

Strings in the code are written in Chinese and wrapped in t(); t() looks them up in the catalog for the
current language and fills {placeholders}. Unknown strings fall back to Chinese, so a missing translation
never breaks the UI (tests check the catalog is complete).
"""

from __future__ import annotations

import ctypes
import locale

from .translations import CATALOG

LANGUAGES = {"zh": "简体中文", "ja": "日本語", "en": "English"}
_current = "zh"


def system_language() -> str:
    """zh / ja / en from the Windows display language (falls back to the locale, then English)."""
    tag = ""
    try:
        buf = ctypes.create_unicode_buffer(85)
        langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
        if ctypes.windll.kernel32.LCIDToLocaleName(langid, buf, 85, 0):
            tag = buf.value
    except (AttributeError, OSError):
        pass
    tag = (tag or locale.getlocale()[0] or "").lower().replace("_", "-")
    if tag.startswith("zh") or tag.startswith("chinese"):
        return "zh"
    if tag.startswith("ja") or tag.startswith("japanese"):
        return "ja"
    return "en"


def set_language(code: str) -> str:
    """Use `code` ("auto" = the system language); returns the language actually used."""
    global _current
    _current = code if code in LANGUAGES else system_language()
    return _current


def current() -> str:
    return _current


def t(text: str, **kw) -> str:
    if _current != "zh":
        text = CATALOG.get(text, {}).get(_current, text)
    return text.format(**kw) if kw else text
