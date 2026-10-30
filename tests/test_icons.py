import struct
import sys
from pathlib import Path

from profile_router import icons

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from fake_site import serve  # noqa: E402


def tiny_png() -> bytes:
    return icons.encode_png(2, 1, b"\x00" + bytes((255, 0, 0, 255, 0, 0, 255, 255)))


def ico(entries: list[tuple[int, int, bytes]]) -> bytes:
    head = struct.pack("<HHH", 0, 1, len(entries))
    offset = 6 + 16 * len(entries)
    dirs, blobs = b"", b""
    for w, bpp, blob in entries:
        dirs += struct.pack("<BBBBHHII", w % 256, w % 256, 0, 0, 1, bpp, len(blob), offset + len(blobs))
        blobs += blob
    return head + dirs + blobs


def bmp32(w: int, h: int, bgra: bytes) -> bytes:
    header = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0, 0, 0, 0, 0, 0)
    return header + bgra + b"\x00" * (((w + 31) // 32) * 4 * h)  # pixels, then the AND mask


def test_png_passthrough_and_ico_with_png():
    png = tiny_png()
    assert icons.to_png(png) == png
    assert icons.to_png(ico([(16, 32, png)])) == png
    assert icons.to_png(b"<svg/>") is None


def test_ico_bmp32_becomes_png():
    # 1x2 image stored bottom-up: bottom pixel blue, top pixel red (BGRA)
    data = ico([(1, 32, bmp32(1, 2, bytes((255, 0, 0, 255, 0, 0, 255, 255))))])
    png = icons.to_png(data)
    assert png and png.startswith(icons.PNG_SIG)
    assert struct.unpack(">II", png[16:24]) == (1, 2)


def test_candidates_prefer_png_links_then_fallbacks():
    html = ('<link rel="shortcut icon" href="/favicon.ico">'
            '<link rel="apple-touch-icon" sizes="180x180" href="/apple.png">'
            '<link rel="icon" href="/logo.svg">')
    got = icons.candidates("https://example.com/", html)
    assert got == ["https://example.com/apple.png", "https://example.com/favicon.ico",
                   "https://example.com/apple-touch-icon.png"]


def test_fetch_icon_from_fake_site(tmp_path, monkeypatch):
    monkeypatch.setenv("PROFILE_ROUTER_CONFIG", str(tmp_path / "config.json"))
    server = serve(port=0, background=True)
    try:
        port = server.server_address[1]
        path = icons.fetch_icon("x.localhost", f"http://x.localhost:{port}/")
    finally:
        server.shutdown()
    assert path == tmp_path / "icons" / "x.localhost.png"
    assert path.read_bytes().startswith(icons.PNG_SIG)
