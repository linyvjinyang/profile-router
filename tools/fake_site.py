"""Fake X / bilibili / PlayStation sites on *.localhost for trying account switching without real accounts.

Each site keeps a login cookie, so every browser profile can be "logged in" as a different account.
Run: python tools/fake_site.py  ->  http://x.localhost:8765/  http://bili.localhost:8765/  http://psn.localhost:8765/
"""

from __future__ import annotations

import html
import sys
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.parse import parse_qs, quote, unquote, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from profile_router.icons import encode_png  # noqa: E402

PORT = 8765
SITES = {
    "x": ("X", "#0F1419"),
    "bili": ("bilibili", "#FB7299"),
    "psn": ("PlayStation", "#0070D1"),
}
SUGGESTED = ("主号", "小号", "工作号")


def site_of(host: str) -> tuple[str, str, str]:
    key = host.split(":")[0].split(".")[0].lower()
    name, color = SITES.get(key, (key or "site", "#444"))
    return key, name, color


def icon_png(color: str, size: int = 64) -> bytes:
    """A site-colored tile with a white square in the middle, so the launcher has a real icon to fetch."""
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    rows = []
    for y in range(size):
        row = bytearray(b"\x00")
        for x in range(size):
            inner = size * 0.3 <= x < size * 0.7 and size * 0.3 <= y < size * 0.7
            row += bytes((255, 255, 255, 255) if inner else (r, g, b, 255))
        rows.append(bytes(row))
    return encode_png(size, size, b"".join(rows))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # keep the console quiet
        pass

    def _account(self) -> str:
        c = SimpleCookie(self.headers.get("Cookie", ""))
        return unquote(c["acct"].value) if "acct" in c else ""

    def _redirect(self, cookie: str) -> None:
        self.send_response(303)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie", cookie)
        self.end_headers()

    def do_GET(self) -> None:
        parts = urlsplit(self.path)
        if parts.path == "/login":
            name = (parse_qs(parts.query).get("as") or [""])[0].strip()[:20]
            if name:
                self._redirect(f"acct={quote(name)}; Path=/; Max-Age=31536000; SameSite=Lax")
                return
        if parts.path == "/logout":
            self._redirect("acct=; Path=/; Max-Age=0")
            return
        if parts.path == "/icon.png":
            data = icon_png(site_of(self.headers.get("Host", ""))[2])
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parts.path != "/":
            self.send_error(404)
            return
        _, name, color = site_of(self.headers.get("Host", ""))
        acct = self._account()
        if acct:
            body = (f'<p class="who" id="account">{html.escape(acct)}</p><p>当前登录的账号</p>'
                    '<p><a href="/logout">退出登录</a></p>')
        else:
            links = " ".join(f'<a class="btn" href="/login?as={quote(s)}">{s}</a>' for s in SUGGESTED)
            body = ('<p id="account" class="none">未登录</p><form action="/login">'
                    '<input name="as" placeholder="随便起个账号名"> <button>登录</button></form>'
                    f'<p>或者：{links}</p>')
        page = f"""<!doctype html><meta charset="utf-8"><title>{name}（测试）</title>
<link rel="icon" type="image/png" sizes="64x64" href="/icon.png">
<style>body{{font-family:"Microsoft YaHei UI",sans-serif;margin:0;background:#f5f6f8}}
header{{background:{color};color:#fff;padding:14px 24px;font-size:20px;font-weight:700}}
main{{padding:32px 24px}}.who{{font-size:44px;font-weight:700;margin:0;color:{color}}}
.none{{font-size:28px;color:#888}}.btn{{display:inline-block;margin:0 6px;padding:4px 12px;border-radius:6px;
background:{color};color:#fff;text-decoration:none}}input,button{{font-size:16px;padding:4px 8px}}</style>
<header>{name} · 测试网站</header><main>{body}</main>"""
        data = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve(port: int = PORT, background: bool = False) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    if background:
        Thread(target=server.serve_forever, daemon=True).start()
    else:
        print(f"http://x.localhost:{port}/  http://bili.localhost:{port}/  http://psn.localhost:{port}/  (Ctrl+C 结束)")
        server.serve_forever()
    return server


if __name__ == "__main__":
    serve()
