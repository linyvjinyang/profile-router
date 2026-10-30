"""Fetch a site's icon and keep it as a PNG Tk can show (Tk reads PNG/GIF, not ICO), with no extra dependencies.

Order: <link rel="icon" / "apple-touch-icon"> on the home page, then /apple-touch-icon.png, then /favicon.ico.
ICO files are unpacked: embedded PNG entries are used as is, 32-bit BMP entries are re-encoded as PNG.
"""

from __future__ import annotations

import gzip
import re
import struct
import urllib.request
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlunsplit

from .config import config_path

PNG_SIG = b"\x89PNG\r\n\x1a\n"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProfileRouter/0.1"
MAX_BYTES = 2_000_000


def icon_dir() -> Path:
    return config_path().parent / "icons"


def icon_path(site: str) -> Path:
    safe = re.sub(r"[^a-z0-9.-]", "_", site.lower())
    return icon_dir() / f"{safe}.png"


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.icons: list[tuple[str, str, str]] = []  # (rel, href, sizes)

    def handle_starttag(self, tag, attrs):
        if tag != "link":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        rel = a.get("rel", "").lower()
        if "icon" in rel and a.get("href"):
            self.icons.append((rel, a["href"], a.get("sizes", "")))


def _get(url: str, timeout: float) -> tuple[str, bytes]:
    final, body = _fetch(url, timeout)
    if body[:2] == b"\x1f\x8b":  # some servers gzip even when not asked to
        try:
            body = gzip.decompress(body)
        except OSError:
            pass
    return final, body


def _fetch(url: str, timeout: float) -> tuple[str, bytes]:
    headers = {"User-Agent": UA, "Accept-Encoding": "identity"}
    parts = urlsplit(url)
    host = parts.hostname or ""
    if host.endswith(".localhost"):  # browsers resolve *.localhost to loopback; Windows DNS does not
        headers["Host"] = parts.netloc
        fetch = urlunsplit(parts._replace(netloc=parts.netloc.replace(host, "127.0.0.1", 1)))
        with urllib.request.urlopen(urllib.request.Request(fetch, headers=headers), timeout=timeout) as r:
            return url, r.read(MAX_BYTES)
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
        return r.geturl(), r.read(MAX_BYTES)


def _size_score(sizes: str) -> int:
    m = re.search(r"(\d+)x\d+", sizes)
    n = int(m.group(1)) if m else 32
    return abs(n - 64)  # prefer around 64px: sharp at 20-32px after integer downscaling


def candidates(page_url: str, html: str) -> list[str]:
    p = _LinkParser()
    try:
        p.feed(html)
    except Exception:  # malformed HTML: use whatever was parsed
        pass
    links = [(href, sizes, rel) for rel, href, sizes in p.icons if not href.lower().endswith(".svg")]
    links.sort(key=lambda x: (not x[0].lower().split("?")[0].endswith(".png"), _size_score(x[1])))
    out = [urljoin(page_url, href) for href, _, _ in links]
    for fallback in ("/apple-touch-icon.png", "/favicon.ico"):
        out.append(urljoin(page_url, fallback))
    return list(dict.fromkeys(out))


def to_png(data: bytes) -> bytes | None:
    if data.startswith(PNG_SIG):
        return data
    if data[:4] == b"\x00\x00\x01\x00":
        return _ico_to_png(data)
    return None


def _ico_to_png(data: bytes) -> bytes | None:
    count = struct.unpack_from("<H", data, 4)[0]
    entries = []
    for i in range(count):
        w, h, _, _, _, bpp, size, offset = struct.unpack_from("<BBBBHHII", data, 6 + 16 * i)
        entries.append(((w or 256), bpp, data[offset:offset + size]))
    entries.sort(key=lambda e: abs(e[0] - 64))
    for _, _, blob in entries:
        if blob.startswith(PNG_SIG):
            return blob
        png = _bmp32_to_png(blob)
        if png:
            return png
    return None


def _bmp32_to_png(blob: bytes) -> bytes | None:
    if len(blob) < 40:
        return None
    header_size, w, h2, _, bpp = struct.unpack_from("<IiiHH", blob, 0)
    h = h2 // 2
    if bpp != 32 or w <= 0 or h <= 0:
        return None
    pixels = blob[header_size:header_size + w * h * 4]
    if len(pixels) < w * h * 4:
        return None
    rows = []
    for y in range(h - 1, -1, -1):  # BMP rows are stored bottom-up, BGRA
        row = pixels[y * w * 4:(y + 1) * w * 4]
        rgba = bytearray(len(row))
        rgba[0::4], rgba[1::4], rgba[2::4], rgba[3::4] = row[2::4], row[1::4], row[0::4], row[3::4]
        rows.append(b"\x00" + bytes(rgba))
    return encode_png(w, h, b"".join(rows))


def encode_png(w: int, h: int, raw_rows: bytes) -> bytes:
    """PNG from RGBA rows that already carry their filter byte."""
    def chunk(kind: bytes, body: bytes) -> bytes:
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return PNG_SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw_rows)) + chunk(b"IEND", b"")


def fetch_icon(site: str, base_url: str | None = None, timeout: float = 6.0) -> Path | None:
    """Download and store the icon for `site`; returns the saved PNG, or None if nothing usable was found."""
    page = base_url or f"https://{site.strip('*.')}/"
    try:
        page, body = _get(page, timeout)
        html = body.decode("utf-8", "replace")
    except Exception:
        html = ""
    for url in candidates(page, html):
        try:
            _, data = _get(url, timeout)
        except Exception:
            continue
        png = to_png(data)
        if png:
            path = icon_path(site)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(png)
            return path
    return None
