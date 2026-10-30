"""Tk launcher. Accounts lead: the main page lists sites and their accounts; each account lives in a room
(a browser profile, grouped by "person"); the second page lists rooms; rare settings sit in a settings window.
See docs/ui-design.md.
"""

from __future__ import annotations

import os
import sqlite3
import threading
import tkinter as tk
from dataclasses import dataclass, replace
from fractions import Fraction
from tkinter import colorchooser, messagebox, simpledialog, ttk

from . import __version__, browsers, i18n, icons, register, shortcuts
from .browsers import Profile
from .i18n import t
from .config import Account, Config, Rule, config_path
from .router import account_urls, accounts_for, host_of, normalize, route

FONT = "Microsoft YaHei UI"
BG = "#F5F6F8"
CARD_BG = "#FFFFFF"
BORDER = "#E3E5EA"
MUTED = "#6B7280"
ICON_PX = 22
SYNC_MS = 2000
SITE_COLORS = ("#4F7BE8", "#E8744F", "#3BA776", "#B65FD6", "#D9A21B", "#2BA3B8", "#D9487A")


def card_title(cfg: Config, p: Profile) -> str:
    c = cfg.cards.get(p.card_id)
    return c.name if c and c.name else p.name


def room_label(cfg: Config, p: Profile) -> str:
    return t("{name}（{browser}）", name=card_title(cfg, p), browser=p.browser_label)


def join_list(items) -> str:
    return t("、").join(items)


def card_subtitle(p: Profile) -> str:
    return p.browser_label + (f" · {p.account}" if p.account else "")


def open_in(cfg: Config, p: Profile, url: str | None = None) -> None:
    if url is None:
        c = cfg.cards.get(p.card_id)
        url = c.home if c and c.home else None
    browsers.launch(p, normalize(url) if url else None)


def site_url(site: str) -> str:
    return normalize(site.strip("*.") + "/")


def room_conflict(cfg: Config, card_id: str, site: str, ignore: Account | None = None) -> Account | None:
    """The account this room already holds on `site`: a room keeps at most one account per site."""
    return next((a for a in cfg.accounts if a.card == card_id and a.site == site and a != ignore), None)


def delete_block_reason(cfg: Config, p: Profile) -> str | None:
    """Why this room must not be deleted, or None if it may be. Main rooms and rooms in use are protected."""
    if p.kind != "chromium":
        return t("只能删除 Chrome、Edge 等 Chromium 系浏览器的房间")
    if p.profile_id == "Default":
        return t("这是浏览器的主房间，不能删除")
    if p.account:
        return t("登录着浏览器账号 {account}，不能删除", account=p.account)
    n = sum(a.card == p.card_id for a in cfg.accounts)
    if n:
        return t("还登记着 {n} 个网站账号，请先在「房间设置」里删除这些账号", n=n)
    return None


@dataclass
class Choice:
    title: str
    subtitle: str
    color: str
    profile: Profile


def profile_choices(cfg: Config, profiles: list[Profile]) -> list[Choice]:
    return [Choice(card_title(cfg, p), card_subtitle(p), cfg.color_for(p.card_id, i), p) for i, p in enumerate(profiles)]


def account_choices(cfg: Config, profiles: list[Profile], accounts: list[Account]) -> list[Choice]:
    index = {p.card_id: i for i, p in enumerate(profiles)}
    out = []
    for a in accounts:
        if a.card in index:
            p = profiles[index[a.card]]
            out.append(Choice(f"{a.site} · {a.label}", t("房间：{room}", room=card_title(cfg, p)), cfg.color_for(p.card_id, index[a.card]), p))
    return out


def decide(url: str, cfg: Config, profiles: list[Profile]) -> tuple[Profile | None, list[Choice], bool]:
    """(profile to open directly, or the choices to ask; whether 'remember for this site' makes sense)."""
    accounts = [a for a in accounts_for(url, cfg.accounts) if any(p.card_id == a.card for p in profiles)]
    if len(accounts) == 1:
        return next(p for p in profiles if p.card_id == accounts[0].card), [], False
    if accounts:
        return None, account_choices(cfg, profiles, accounts), False
    target = route(url, cfg.rules) or ("" if cfg.ask_unmatched else cfg.fallback)
    p = next((x for x in profiles if x.card_id == target), None)
    return (p, [], False) if p else (None, profile_choices(cfg, profiles), True)


def _style(root: tk.Misc) -> None:
    s = ttk.Style(root)
    s.configure("TFrame", background=BG)
    s.configure("TLabel", background=BG, font=(FONT, 10))
    s.configure("TButton", font=(FONT, 10))
    s.configure("TCheckbutton", background=BG, font=(FONT, 10))
    s.configure("TRadiobutton", background=BG, font=(FONT, 10))
    s.configure("TNotebook.Tab", font=(FONT, 10), padding=(14, 4))
    s.configure("Toolbutton", font=(FONT, 11), padding=(16, 5))
    s.configure("Muted.TLabel", foreground=MUTED, background=BG, font=(FONT, 9))
    s.configure("Head.TLabel", background=BG, font=(FONT, 11, "bold"))


def _dialog(parent: tk.Misc, title: str) -> tuple[tk.Toplevel, ttk.Frame]:
    win = tk.Toplevel(parent)
    win.title(title)
    win.configure(bg=BG)
    win.transient(parent)
    f = ttk.Frame(win, padding=16)
    f.pack(fill="both", expand=True)
    return win, f


def _scroll_area(parent: tk.Misc, height: int | None = None, bg: str = BG) -> tuple[tk.Frame, tk.Frame]:
    """(outer frame to place, inner frame to fill); the inner frame scrolls vertically and follows the width."""
    outer = tk.Frame(parent, bg=bg)
    size = {"height": height, "width": 480} if height else {}
    canvas = tk.Canvas(outer, bg=bg, highlightthickness=0, **size)
    bar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    window = canvas.create_window((0, 0), window=inner, anchor="nw")
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfigure(window, width=e.width))
    canvas.configure(yscrollcommand=bar.set)
    canvas.pack(side="left", fill="both", expand=True)
    bar.pack(side="right", fill="y")
    wheel = lambda ev: canvas.yview_scroll(-ev.delta // 120, "units")  # noqa: E731
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", wheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
    inner.canvas = canvas  # type: ignore[attr-defined]
    return outer, inner


class ExtensionPicker(ttk.Frame):
    """Pick extensions installed in an existing room; each one is installed by opening its store page."""

    def __init__(self, parent: tk.Misc, cfg: Config, rooms: list[Profile], height: int = 170):
        super().__init__(parent)
        self.cfg = cfg
        self.sources = {room_label(cfg, p): p for p in rooms if p.kind == "chromium"}
        top = ttk.Frame(self)
        top.pack(fill="x")
        ttk.Label(top, text=t("扩展，复制自")).pack(side="left")
        self.source = tk.StringVar(value=self._default_source())
        box = ttk.Combobox(top, textvariable=self.source, values=list(self.sources), state="readonly", width=24)
        box.pack(side="left", padx=6)
        box.bind("<<ComboboxSelected>>", lambda e: self._fill())
        ttk.Button(top, text=t("全不选"), command=lambda: self._set_all(False)).pack(side="right")
        ttk.Button(top, text=t("全选"), command=lambda: self._set_all(True)).pack(side="right", padx=4)
        outer, self.list = _scroll_area(self, height=height, bg=CARD_BG)
        outer.configure(highlightthickness=1, highlightbackground=BORDER)
        outer.pack(fill="both", expand=True, pady=(4, 0))
        known = browsers.PASSWORD_MANAGERS  # older configs stored manager names instead of ids
        self.remembered = {known.get(x, x) for x in cfg.new_profile_extensions}
        self.checks: dict[str, tuple[tk.BooleanVar, browsers.Extension]] = {}
        self._fill()

    def _default_source(self) -> str:
        if not self.sources:
            return ""
        return max(self.sources, key=lambda k: len(browsers.list_extensions(self.sources[k])))

    def _fill(self) -> None:
        for w in self.list.winfo_children():
            w.destroy()
        self.checks = {}
        p = self.sources.get(self.source.get())
        managers = set(browsers.PASSWORD_MANAGERS.values())
        exts = sorted(browsers.list_extensions(p) if p else [], key=lambda e: (e.id not in managers, e.name.lower()))
        if not exts:
            tk.Label(self.list, text=t("这个房间没有可复制的扩展"), bg=CARD_BG, fg=MUTED, font=(FONT, 9)).pack(anchor="w", padx=6)
        for e in exts:
            v = tk.BooleanVar(value=e.id in self.remembered if self.remembered else e.id in managers)
            if e.id in managers:
                text = t("{name}（已停用）  · 密码管理器", name=e.name) if not e.enabled else \
                    t("{name}  · 密码管理器", name=e.name)
            else:
                text = t("{name}（已停用）", name=e.name) if not e.enabled else e.name
            tk.Checkbutton(self.list, text=text, variable=v, bg=CARD_BG, activebackground=CARD_BG, anchor="w",
                           font=(FONT, 10)).pack(fill="x", padx=6)
            self.checks[e.id] = (v, e)

    def _set_all(self, value: bool) -> None:
        for v, _ in self.checks.values():
            v.set(value)

    def selected(self) -> list[browsers.Extension]:
        return [e for v, e in self.checks.values() if v.get()]


class LauncherApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.cfg = Config.load()
        self.profiles: list[Profile] = []
        self.icon_cache: dict[str, tk.PhotoImage] = {}
        self.icon_tried: set[str] = set()
        self.show_hidden = False
        root.title(t("浏览器账号切换"))
        root.configure(bg=BG)
        root.minsize(760, 480)
        _style(root)
        self._build()
        self.refresh()
        self.root.after(SYNC_MS, self._poll)

    def rebuild(self) -> None:
        """Redraw the whole window, e.g. after the UI language changed."""
        page = self.page.get()
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title(t("浏览器账号切换"))
        _style(self.root)
        self._build()
        self.page.set(page)
        self.refresh()

    # --- frame -----------------------------------------------------------------------------------

    def _build(self) -> None:
        top = ttk.Frame(self.root, padding=(16, 14, 16, 8))
        top.pack(fill="x")
        self.page = tk.StringVar(value="accounts")
        for key, text in (("accounts", t("账号")), ("rooms", t("房间"))):
            ttk.Radiobutton(top, text=text, value=key, variable=self.page, style="Toolbutton",
                            command=self.render).pack(side="left")
        ttk.Button(top, text=t("⚙ 设置"), command=self.open_settings).pack(side="right")
        self.search = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search, font=(FONT, 10))
        entry.pack(side="left", fill="x", expand=True, padx=12)
        entry.bind("<Return>", lambda e: self.search_enter())
        self.search.trace_add("write", lambda *a: self.page.get() == "accounts" and self.render())
        self._placeholder(entry, t("搜索网站或账号，或粘贴网址回车"))

        outer, self.content = _scroll_area(self.root)
        outer.pack(fill="both", expand=True, padx=16)
        self.status = ttk.Label(self.root, style="Muted.TLabel", padding=(16, 4, 16, 10))
        self.status.pack(fill="x")

    def _placeholder(self, entry: ttk.Entry, text: str) -> None:
        hint = tk.Label(entry, text=text, fg="#9CA3AF", bg="white", font=(FONT, 10))

        def update(*_):
            if self.search.get() or self.root.focus_get() is entry:
                hint.place_forget()
            else:
                hint.place(x=6, rely=0.5, anchor="w")

        hint.bind("<Button-1>", lambda e: entry.focus_set())
        entry.bind("<FocusIn>", update, add="+")
        entry.bind("<FocusOut>", update, add="+")
        self.search.trace_add("write", update)
        self.root.after(50, update)

    def refresh(self) -> None:
        self.cfg = Config.load()
        self.profiles = browsers.all_profiles(self.cfg.extra_profiles)
        self._watch = browsers.watched_files(self.cfg.extra_profiles) + [config_path()]
        self._seen = browsers.signature(self._watch)
        self._known = self._state(self.profiles)
        self.render()

    @staticmethod
    def _state(profiles: list[Profile]) -> tuple:
        return tuple((p.card_id, p.name, p.account) for p in profiles) + (browsers.signature([config_path()]),)

    def _poll(self) -> None:
        """Sync without restarting. Browsers rewrite their profile list file often, so a changed file only
        triggers a re-read; the window is redrawn only when rooms (or our settings file) really changed."""
        try:
            sig = browsers.signature(self._watch)
            if self.cfg.auto_sync and sig != self._seen:
                self._seen = sig
                profiles = browsers.all_profiles(Config.load().extra_profiles)
                if self._state(profiles) != self._known:
                    before = {p.card_id for p in self.profiles}
                    self.refresh()
                    added = [card_title(self.cfg, p) for p in self.profiles if p.card_id not in before]
                    self.status.config(text=t("已同步：新房间 {names}", names=join_list(added)) if added
                                       else t("已同步浏览器里的变化"))
        finally:
            self.root.after(SYNC_MS, self._poll)

    def sync_now(self) -> None:
        self.refresh()
        self.status.config(text=t("已同步"))

    @property
    def rooms(self) -> list[Profile]:
        return [p for p in self.profiles if p.card_id not in self.cfg.hidden_rooms]

    def room_of(self, a: Account) -> Profile | None:
        return next((p for p in self.profiles if p.card_id == a.card), None)

    def color_of(self, card_id: str) -> str:
        i = next((n for n, p in enumerate(self.profiles) if p.card_id == card_id), None)
        return self.cfg.color_for(card_id, i) if i is not None else "#9CA3AF"

    def render(self) -> None:
        for w in self.content.winfo_children():
            w.destroy()
        self.content.canvas.yview_moveto(0)
        (self._rooms_page if self.page.get() == "rooms" else self._accounts_page)()
        self.status.config(text=t("{sites} 个网站 · {accounts} 个账号 · {rooms} 个房间",
                                  sites=len(self.cfg.site_order()), accounts=len(self.cfg.accounts),
                                  rooms=len(self.rooms)))

    # --- accounts page ---------------------------------------------------------------------------

    def _accounts_page(self) -> None:
        q = self.search.get().strip().lower()
        sites = self.cfg.site_order()
        shown = [s for s in sites if not q or q in s or any(q in a.label.lower() for a in self.cfg.accounts if a.site == s)]
        if not sites:
            ttk.Label(self.content, text=t("还没有账号。\n① 在下面添加一个网站（如 x.com）\n② 点那一行的「＋」给它加账号，"
                                           "选一个房间或新建房间，在打开的页面里登录一次"),
                      style="Muted.TLabel", justify="left").pack(anchor="w", pady=8)
        elif not shown:
            ttk.Label(self.content, text=t("没有匹配「{q}」的网站或账号；回车可当网址打开。", q=q),
                      style="Muted.TLabel").pack(anchor="w", pady=8)
        for site in shown:
            self._site_row(site, q)
        add = ttk.Frame(self.content)
        add.pack(fill="x", pady=(12, 4))
        self.new_site = tk.StringVar()
        e = ttk.Entry(add, textvariable=self.new_site, width=32, font=(FONT, 10))
        e.pack(side="left")
        e.bind("<Return>", lambda ev: self.add_site())
        ttk.Button(add, text=t("＋ 添加网站"), command=self.add_site).pack(side="left", padx=6)
        ttk.Label(add, text=t("输入网址，会自动获取网站图标"), style="Muted.TLabel").pack(side="left")

    def _site_row(self, site: str, q: str) -> None:
        row = tk.Frame(self.content, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
        row.pack(fill="x", pady=4)
        self._icon_widget(row, site).pack(side="left", padx=(12, 8), pady=10)
        name = tk.Label(row, text=site, bg=CARD_BG, font=(FONT, 11, "bold"), width=17, anchor="w")
        name.pack(side="left")
        accts = [a for a in self.cfg.accounts if a.site == site]
        for a in accts:
            self._account_button(row, a, dim=bool(q) and q not in site and q not in a.label.lower()).pack(
                side="left", padx=(0, 6))
        if not accts:
            tk.Label(row, text=t("还没有账号"), bg=CARD_BG, fg=MUTED, font=(FONT, 9)).pack(side="left")
        more = ttk.Button(row, text="⋯", width=3)
        more.pack(side="right", padx=(0, 8))
        ttk.Button(row, text="＋", width=3, command=lambda: self.add_account(site)).pack(side="right", padx=4)
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=t("添加账号…"), command=lambda: self.add_account(site))
        menu.add_command(label=t("重新获取图标"), command=lambda: self.refetch_icon(site))
        menu.add_separator()
        menu.add_command(label=t("移除这个网站…"), command=lambda: self.remove_site(site))
        more.configure(command=lambda: menu.tk_popup(more.winfo_rootx(), more.winfo_rooty() + more.winfo_height()))
        for w in (row, name):
            w.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _account_button(self, parent: tk.Misc, a: Account, dim: bool = False) -> tk.Button:
        color = "#C9CDD4" if dim else self.color_of(a.card)
        room = self.room_of(a)
        b = tk.Button(parent, text=a.label, bg=color, fg="white", activebackground=color, activeforeground="white",
                      relief="flat", font=(FONT, 10, "bold"), padx=12, pady=3, bd=0, cursor="hand2",
                      command=lambda: self.switch(a))
        b.bind("<Button-3>", lambda e: self._account_menu(a).tk_popup(e.x_root, e.y_root))
        where = card_title(self.cfg, room) if room else t("（找不到）")
        if a.pages:
            hover = t("{site} · {label}  →  房间「{room}」 · 打开 {n} 个常用页", site=a.site, label=a.label,
                      room=where, n=len(a.pages))
        else:
            hover = t("{site} · {label}  →  房间「{room}」", site=a.site, label=a.label, room=where)
        b.bind("<Enter>", lambda e: self.status.config(text=hover))
        return b

    def _account_menu(self, a: Account) -> tk.Menu:
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=t("打开"), command=lambda: self.switch(a))
        menu.add_command(label=t("常用页…（{n}）", n=len(a.pages)) if a.pages else t("常用页…"),
                         command=lambda: PagesDialog(self.root, a, on_saved=lambda new: self._replace_account(a, new)))
        menu.add_command(label=t("创建快捷方式…"), command=lambda: ShortcutDialog(self.root, self, a))
        menu.add_command(label=t("改名…"), command=lambda: self.rename_account(a))
        move = tk.Menu(menu, tearoff=0)
        for p in self.rooms:
            clash = room_conflict(self.cfg, p.card_id, a.site, ignore=a)
            title = card_title(self.cfg, p)
            label = t("{room}（当前）", room=title) if p.card_id == a.card else \
                t("{room}（已有 {label}）", room=title, label=clash.label) if clash else title
            move.add_command(label=label, state="disabled" if clash or p.card_id == a.card else "normal",
                             command=lambda p=p: self.move_account(a, p))
        menu.add_cascade(label=t("移到房间"), menu=move)
        menu.add_separator()
        menu.add_command(label=t("删除这个账号"), command=lambda: self.delete_account(a))
        return menu

    def switch(self, a: Account) -> None:
        p = self.room_of(a)
        if not p:
            messagebox.showwarning(t("切换账号"), t("找不到「{label}」所在的房间（{card}）。", label=a.label, card=a.card))
            return
        urls = account_urls(a)
        browsers.launch(p, *urls)
        if a.pages:
            text = t("已切到 {site} · {label}（房间「{room}」），打开了 {n} 个常用页", site=a.site, label=a.label,
                     room=card_title(self.cfg, p), n=len(urls))
        else:
            text = t("已切到 {site} · {label}（房间「{room}」）", site=a.site, label=a.label, room=card_title(self.cfg, p))
        self.status.config(text=text)

    def search_enter(self) -> None:
        text = self.search.get().strip()
        if "." in text and " " not in text:
            self.open_url(text)

    def open_url(self, text: str) -> None:
        url = normalize(text)
        p, choices, remember = decide(url, self.cfg, self.rooms)
        if p:
            open_in(self.cfg, p, url)
            self.status.config(text=t("用房间「{room}」打开", room=card_title(self.cfg, p)))
        else:
            Picker(tk.Toplevel(self.root), url, self.cfg, choices, remember, on_done=self.refresh)

    def add_site(self) -> None:
        raw = self.new_site.get().strip().lower()
        site = host_of(raw) if raw else ""
        if not site:
            return
        if site not in self.cfg.sites:
            self.cfg.sites.append(site)
            self.cfg.save()
        self.icon_tried.discard(site)
        self.render()
        self.status.config(text=t("已添加 {site}，正在获取图标…", site=site))

    def remove_site(self, site: str) -> None:
        accts = [a for a in self.cfg.accounts if a.site == site]
        if accts:
            DeleteAccountsDialog(self.root, self.cfg, self.profiles, accts, on_done=self._accounts_deleted,
                                 remove_site=site)
            return
        if messagebox.askyesno(t("移除网站"), t("移除 {site}？", site=site)):
            self.cfg.sites = [s for s in self.cfg.sites if s != site]
            self.cfg.save()
            self.render()

    def delete_account(self, a: Account, after=None) -> None:
        DeleteAccountsDialog(self.root, self.cfg, self.profiles, [a],
                             on_done=lambda text: (self._accounts_deleted(text), after and after()))

    def _accounts_deleted(self, text: str) -> None:
        self.refresh()
        self.status.config(text=text)

    def add_account(self, site: str) -> None:
        AddAccountDialog(self.root, self.cfg, self.rooms, site, on_done=self._after_add)

    def _after_add(self, text: str, new_room: bool) -> None:
        self.refresh()
        self.status.config(text=text)
        if new_room:  # the browser registers the new profile shortly after it opens
            self.root.after(4000, self.refresh)

    def rename_account(self, a: Account) -> None:
        name = simpledialog.askstring(t("改名"), t("{site} 的账号名：", site=a.site), initialvalue=a.label,
                                      parent=self.root)
        if name and name.strip():
            self._replace_account(a, replace(a, label=name.strip()))

    def move_account(self, a: Account, p: Profile) -> None:
        if messagebox.askyesno(t("移到房间"), t("把 {site} · {label} 登记到房间「{room}」？\n"
                                              "只改登记；那个房间里还要登录一次这个账号。",
                                              site=a.site, label=a.label, room=card_title(self.cfg, p))):
            self._replace_account(a, replace(a, card=p.card_id))

    def _replace_account(self, old: Account, new: Account) -> None:
        self.cfg.accounts = [new if x == old else x for x in self.cfg.accounts]
        self.cfg.save()
        self.render()

    # --- icons -----------------------------------------------------------------------------------

    def _icon_widget(self, parent: tk.Misc, site: str) -> tk.Widget:
        img = self._icon_image(site)
        if img:
            return tk.Label(parent, image=img, bg=parent["bg"])
        c = tk.Canvas(parent, width=ICON_PX, height=ICON_PX, bg=parent["bg"], highlightthickness=0)
        c.create_oval(1, 1, ICON_PX - 1, ICON_PX - 1, fill=SITE_COLORS[sum(map(ord, site)) % len(SITE_COLORS)],
                      outline="")
        c.create_text(ICON_PX / 2, ICON_PX / 2, text=site.strip("*.")[:1].upper(), fill="white", font=(FONT, 9, "bold"))
        self._fetch_icon_later(site)
        return c

    def _icon_image(self, site: str) -> tk.PhotoImage | None:
        if site in self.icon_cache:
            return self.icon_cache[site]
        path = icons.icon_path(site)
        if not path.is_file():
            return None
        try:
            img = tk.PhotoImage(file=str(path))
        except tk.TclError:
            return None
        if img.width() > ICON_PX:  # Tk only scales by integers: zoom by n, then subsample by d
            r = Fraction(ICON_PX, img.width()).limit_denominator(64)
            img = (img.zoom(r.numerator) if r.numerator > 1 else img).subsample(r.denominator)
        self.icon_cache[site] = img
        return img

    def _fetch_icon_later(self, site: str) -> None:
        if site in self.icon_tried:
            return
        self.icon_tried.add(site)
        base = next((a.url for a in self.cfg.accounts if a.site == site and a.url), None)

        def work() -> None:
            if icons.fetch_icon(site, base):
                self.root.after(0, self._icon_ready, site)

        threading.Thread(target=work, daemon=True).start()

    def _icon_ready(self, site: str) -> None:
        self.icon_cache.pop(site, None)
        self.render()

    def refetch_icon(self, site: str) -> None:
        icons.icon_path(site).unlink(missing_ok=True)
        self.icon_cache.pop(site, None)
        self.icon_tried.discard(site)
        self.render()

    # --- rooms page ------------------------------------------------------------------------------

    def _rooms_page(self) -> None:
        for p in self.rooms:
            self._room_row(p, hidden=False)
        hidden = [p for p in self.profiles if p.card_id in self.cfg.hidden_rooms]
        bar = ttk.Frame(self.content)
        bar.pack(fill="x", pady=(12, 4))
        ttk.Button(bar, text=t("＋ 新建房间"), command=self.new_room).pack(side="left")
        if hidden:
            ttk.Button(bar, text=t("收起已隐藏的 {n} 个房间", n=len(hidden)) if self.show_hidden else
                       t("显示已隐藏的 {n} 个房间", n=len(hidden)),
                       command=self._toggle_hidden).pack(side="right")
        if hidden and self.show_hidden:
            for p in hidden:
                self._room_row(p, hidden=True)

    def _room_row(self, p: Profile, hidden: bool) -> None:
        row = tk.Frame(self.content, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER)
        row.pack(fill="x", pady=4)
        tk.Frame(row, bg="#C9CDD4" if hidden else self.color_of(p.card_id), width=6).pack(side="left", fill="y")
        head = tk.Frame(row, bg=CARD_BG, padx=12, pady=8)
        head.pack(side="left", fill="y")
        name = tk.Label(head, text=card_title(self.cfg, p), bg=CARD_BG, font=(FONT, 11, "bold"), anchor="w", width=16)
        name.pack(fill="x")
        tk.Label(head, text=p.browser_label, bg=CARD_BG, fg=MUTED, font=(FONT, 9), anchor="w").pack(fill="x")
        chips = tk.Frame(row, bg=CARD_BG)
        chips.pack(side="left", fill="x", expand=True, pady=8)
        accts = [a for a in self.cfg.accounts if a.card == p.card_id]
        if not accts:
            tk.Label(chips, text=t("还没有账号"), bg=CARD_BG, fg=MUTED, font=(FONT, 9)).pack(side="left", pady=6)
        for a in accts:
            chip = tk.Frame(chips, bg=CARD_BG, cursor="hand2")
            chip.pack(side="left", padx=(0, 14))
            self._icon_widget(chip, a.site).pack(side="left", padx=(0, 4))
            lbl = tk.Label(chip, text=a.label, bg=CARD_BG, font=(FONT, 10), cursor="hand2")
            lbl.pack(side="left")
            for w in (chip, lbl):
                w.bind("<Button-1>", lambda e, a=a: self.switch(a))
                w.bind("<Button-3>", lambda e, a=a: self._account_menu(a).tk_popup(e.x_root, e.y_root))
        if hidden:
            ttk.Button(row, text=t("恢复"), command=lambda: self._set_hidden(p, False)).pack(side="right", padx=8)
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=t("打开这个房间"), command=lambda: self._open(p))
        menu.add_command(label=t("房间设置（名字、颜色、账号）…"), command=lambda: self.room_settings(p))
        menu.add_command(label=t("创建快捷方式…"), command=lambda: ShortcutDialog(self.root, self, p))
        if p.kind == "chromium":
            menu.add_command(label=t("复制扩展到这个房间…"),
                             command=lambda: CopyExtensionsDialog(self.root, self.cfg, self.rooms, p))
        menu.add_separator()
        menu.add_command(label=t("从列表隐藏"), command=lambda: self._set_hidden(p, True))
        blocked = delete_block_reason(self.cfg, p)
        menu.add_command(label=t("删除这个房间…") if not blocked else t("删除这个房间（{reason}）", reason=blocked),
                         state="disabled" if blocked else "normal", command=lambda: self.delete_room(p))
        more = ttk.Button(row, text="⋯", width=3)
        more.configure(command=lambda: menu.tk_popup(more.winfo_rootx(), more.winfo_rooty() + more.winfo_height()))
        more.pack(side="right", padx=(0, 8))
        ttk.Button(row, text=t("打开"), command=lambda: self._open(p)).pack(side="right", padx=4)
        for w in (row, head, name):
            w.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _open(self, p: Profile) -> None:
        open_in(self.cfg, p)
        self.status.config(text=t("已打开房间「{room}」", room=card_title(self.cfg, p)))

    def room_settings(self, p: Profile) -> None:
        RoomDialog(self.root, self, p)

    def delete_room(self, p: Profile) -> None:
        blocked = delete_block_reason(self.cfg, p)
        if blocked:
            messagebox.showinfo(t("删除房间"), blocked)
            return
        if browsers.is_running(p.exe):
            messagebox.showinfo(t("删除房间"), t("请先关闭 {browser} 的所有窗口，再删除房间。\n"
                                               "浏览器开着时删除，它可能把这个用户又写回去。", browser=p.browser_label))
            return
        name = card_title(self.cfg, p)
        if not messagebox.askyesno(
                t("删除房间"), t("删除房间「{name}」（{browser}）？\n\n"
                                 "这个浏览器用户的文件夹（书签、扩展、浏览记录、登录状态）会移到回收站，"
                                 "需要时可以从回收站还原。", name=name, browser=p.browser_label), icon="warning"):
            return
        try:
            browsers.delete_profile(p)
        except OSError as e:
            messagebox.showerror(t("删除房间"), str(e))
            return
        self.cfg.forget_room(p.card_id)
        self.cfg.save()
        self.refresh()
        self.status.config(text=t("已删除房间「{name}」，文件夹在回收站里", name=name))

    def _toggle_hidden(self) -> None:
        self.show_hidden = not self.show_hidden
        self.render()

    def _set_hidden(self, p: Profile, hidden: bool) -> None:
        rest = [c for c in self.cfg.hidden_rooms if c != p.card_id]
        self.cfg.hidden_rooms = rest + [p.card_id] if hidden else rest
        self.cfg.save()
        self.render()

    def new_room(self) -> None:
        if not browsers.installed_chromium():
            messagebox.showinfo(t("新建房间"), t("没有找到可新建用户的浏览器（支持 Chrome、Edge、Brave、Vivaldi、Iron）。"))
            return
        NewRoomDialog(self.root, self.cfg, self.rooms, on_done=self._after_add)

    def open_settings(self) -> None:
        SettingsDialog(self.root, self.cfg, self.rooms, on_saved=self.refresh, on_sync=self.sync_now,
                       on_language=self.rebuild)


def _new_room_fields(parent: ttk.Frame, cfg: Config, rooms: list[Profile], name: str):
    """Name + browser + extension picker for a new room; returns (frame, name var, browser var, picker)."""
    specs = browsers.installed_chromium()
    box = ttk.Frame(parent)
    row = ttk.Frame(box)
    row.pack(fill="x")
    ttk.Label(row, text=t("房间名")).pack(side="left")
    name_var = tk.StringVar(value=name)
    ttk.Entry(row, textvariable=name_var, width=18).pack(side="left", padx=6)
    ttk.Label(row, text=t("浏览器")).pack(side="left", padx=(10, 0))
    browser_var = tk.StringVar(value=specs[0].label if specs else "")
    ttk.Combobox(row, textvariable=browser_var, values=[s.label for s in specs], state="readonly", width=10).pack(
        side="left", padx=6)
    picker = ExtensionPicker(box, cfg, rooms, height=140)
    picker.pack(fill="both", expand=True, pady=(8, 0))
    ttk.Label(box, text=t("新房间是本地用户，不会弹出浏览器的登录、设置页面；勾选的扩展会打开商店页，点一下「添加」。"
                          "Windows Hello 里的通行密钥所有房间都能直接用。"),
              style="Muted.TLabel", wraplength=520, justify="left").pack(anchor="w", pady=(6, 0))
    return box, name_var, browser_var, picker


def _create_room(name: str, browser_label: str, picker: ExtensionPicker, cfg: Config, extra_urls=()) -> str:
    spec = next(s for s in browsers.installed_chromium() if s.label == browser_label)
    chosen = picker.selected()
    name = name or t("新房间")
    d = browsers.create_local_profile(spec, name, tuple(e.url for e in chosen) + tuple(extra_urls))
    cfg.new_profile_extensions = [e.id for e in chosen]
    card_id = f"{spec.key}:{d}"
    cfg.card(card_id).name = name
    return card_id


class AddAccountDialog:
    """The one way to add an account: name it, pick a room (or make a new one), then log in once."""

    def __init__(self, parent: tk.Misc, cfg: Config, rooms: list[Profile], site: str, on_done):
        self.cfg, self.rooms, self.site, self.on_done = cfg, rooms, site, on_done
        title = t("给 {site} 添加账号", site=site)
        self.win, f = _dialog(parent, title)
        ttk.Label(f, text=title, style="Head.TLabel").pack(anchor="w")
        row = ttk.Frame(f)
        row.pack(fill="x", pady=(10, 6))
        ttk.Label(row, text=t("账号名")).pack(side="left")
        self.label = tk.StringVar()
        e = ttk.Entry(row, textvariable=self.label, width=24, font=(FONT, 10))
        e.pack(side="left", padx=8)
        e.focus_set()
        ttk.Label(row, text=t("自己认得出就行，如「小号」"), style="Muted.TLabel").pack(side="left")

        ttk.Label(f, text=t("放在哪个房间里：")).pack(anchor="w", pady=(6, 2))
        self.choice = tk.StringVar()
        first_free = ""
        for p in rooms:
            clash = room_conflict(cfg, p.card_id, site)
            others = [f"{a.site} {a.label}" for a in cfg.accounts if a.card == p.card_id]
            note = t("已有 {site} {label}，同一房间不能放同网站两个账号", site=site, label=clash.label) if clash \
                else t("已有：{accounts}", accounts=join_list(others)) if others else t("空房间")
            line = ttk.Frame(f)
            line.pack(fill="x")
            ttk.Radiobutton(line, text=room_label(cfg, p), value=p.card_id,
                            variable=self.choice, command=self._toggle,
                            state="disabled" if clash else "normal").pack(side="left")
            ttk.Label(line, text="  " + note, style="Muted.TLabel").pack(side="left")
            first_free = first_free or ("" if clash else p.card_id)
        new_ok = bool(browsers.installed_chromium())
        ttk.Radiobutton(f, text=t("新建房间"), value="__new__", variable=self.choice, command=self._toggle,
                        state="normal" if new_ok else "disabled").pack(anchor="w", pady=(4, 0))
        self.new_box, self.room_name, self.browser, self.picker = _new_room_fields(f, cfg, rooms, "")
        self.label.trace_add("write", lambda *a: self.room_name.set(self.label.get()))
        self.choice.set("__new__" if new_ok and not first_free else first_free)
        buttons = ttk.Frame(f)
        buttons.pack(fill="x", side="bottom", pady=(12, 0))
        ttk.Button(buttons, text=t("添加并打开登录页"), command=self.submit).pack(side="right")
        ttk.Button(buttons, text=t("取消"), command=self.win.destroy).pack(side="right", padx=6)
        self._toggle()

    def _toggle(self) -> None:
        if self.choice.get() == "__new__":
            self.new_box.pack(fill="both", expand=True, padx=(22, 0), pady=(4, 0))
        else:
            self.new_box.pack_forget()

    def submit(self) -> None:
        label = self.label.get().strip()
        if not label or not self.choice.get():
            messagebox.showwarning(t("添加账号"), t("请填写账号名，并选择房间。"), parent=self.win)
            return
        url = site_url(self.site)
        if self.choice.get() == "__new__":
            card_id = _create_room(self.room_name.get().strip() or label, self.browser.get(), self.picker, self.cfg,
                                   (url,))
            new_room = True
        else:
            card_id = self.choice.get()
            browsers.launch(next(p for p in self.rooms if p.card_id == card_id), url)
            new_room = False
        self.cfg.accounts.append(Account(self.site, label, card_id))
        if self.site not in self.cfg.sites:
            self.cfg.sites.append(self.site)
        self.cfg.save()
        self.win.destroy()
        self.on_done(t("已添加 {site} · {label}，请在打开的页面里登录", site=self.site, label=label), new_room)


class NewRoomDialog:
    def __init__(self, parent: tk.Misc, cfg: Config, rooms: list[Profile], on_done):
        self.cfg, self.on_done = cfg, on_done
        self.win, f = _dialog(parent, t("新建房间"))
        box, self.name, self.browser, self.picker = _new_room_fields(f, cfg, rooms, t("房间 {n}", n=len(rooms) + 1))
        box.pack(fill="both", expand=True)
        ttk.Button(f, text=t("创建并打开"), command=self.submit).pack(anchor="e", pady=(12, 0))

    def submit(self) -> None:
        name = self.name.get().strip() or t("新房间")
        _create_room(name, self.browser.get(), self.picker, self.cfg)
        self.cfg.save()
        self.win.destroy()
        self.on_done(t("已新建房间「{name}」", name=name), True)


class CopyExtensionsDialog:
    def __init__(self, parent: tk.Misc, cfg: Config, rooms: list[Profile], target: Profile):
        self.target = target
        self.win, f = _dialog(parent, t("复制扩展到「{room}」", room=card_title(cfg, target)))
        others = [p for p in rooms if p.card_id != target.card_id]
        self.picker = ExtensionPicker(f, cfg, others)
        self.picker.pack(fill="both", expand=True)
        ttk.Label(f, text=t("会在这个房间里打开勾选扩展的商店页，每个点一下「添加」。"), style="Muted.TLabel").pack(
            anchor="w", pady=(6, 0))
        ttk.Button(f, text=t("打开商店页"), command=self.submit).pack(anchor="e", pady=(12, 0))

    def submit(self) -> None:
        for e in self.picker.selected():
            browsers.launch(self.target, e.url)
        self.win.destroy()


class PagesDialog:
    """The pages an account opens together when you switch to it (its own bookmarks)."""

    def __init__(self, parent: tk.Misc, a: Account, on_saved):
        self.a, self.on_saved = a, on_saved
        self.win, f = _dialog(parent, t("{site} · {label} 的常用页", site=a.site, label=a.label))
        ttk.Label(f, text=t("切到「{label}」时，这些页面会在它的房间里一起打开；没有常用页时打开网站首页。", label=a.label),
                  style="Muted.TLabel", wraplength=460).pack(anchor="w")
        body = ttk.Frame(f)
        body.pack(fill="both", expand=True, pady=8)
        self.list = tk.Listbox(body, height=8, width=56, font=(FONT, 10), activestyle="none",
                               highlightthickness=1, highlightcolor=BORDER, relief="flat")
        self.list.pack(side="left", fill="both", expand=True)
        side = ttk.Frame(body)
        side.pack(side="left", fill="y", padx=(8, 0))
        ttk.Button(side, text=t("上移"), command=lambda: self.move(-1)).pack(fill="x")
        ttk.Button(side, text=t("下移"), command=lambda: self.move(1)).pack(fill="x", pady=4)
        ttk.Button(side, text=t("删除"), command=self.remove).pack(fill="x")
        add = ttk.Frame(f)
        add.pack(fill="x")
        self.url = tk.StringVar(value=f"https://{a.site.strip('*.')}/")
        e = ttk.Entry(add, textvariable=self.url, font=(FONT, 10))
        e.pack(side="left", fill="x", expand=True)
        e.bind("<Return>", lambda ev: self.add())
        ttk.Button(add, text=t("添加"), command=self.add).pack(side="left", padx=(6, 0))
        ttk.Button(f, text=t("保存"), command=self.save).pack(anchor="e", pady=(12, 0))
        for u in a.pages:
            self.list.insert("end", u)

    def add(self) -> None:
        url = normalize(self.url.get())
        if url and url not in self.list.get(0, "end"):
            self.list.insert("end", url)
        self.url.set("")

    def remove(self) -> None:
        for i in reversed(self.list.curselection()):
            self.list.delete(i)

    def move(self, step: int) -> None:
        sel = self.list.curselection()
        if not sel:
            return
        i, j = sel[0], sel[0] + step
        if 0 <= j < self.list.size():
            text = self.list.get(i)
            self.list.delete(i)
            self.list.insert(j, text)
            self.list.selection_set(j)

    def save(self) -> None:
        self.win.destroy()
        self.on_saved(replace(self.a, pages=list(self.list.get(0, "end"))))


class ShortcutDialog:
    """Create desktop / Start menu shortcuts that open an account (its pages, in its room) or a room.
    The launch target is pre-filled from where the dialog was opened and can be changed from the list."""

    def __init__(self, parent: tk.Misc, launcher: LauncherApp, preset: Account | Profile | None = None):
        self.launcher = launcher
        cfg = launcher.cfg
        self.items: dict[str, tuple[Profile, list[str], str, str]] = {}  # label -> (room, urls, name, site)
        preset_label = ""
        for a in cfg.accounts:
            p = launcher.room_of(a)
            if p:
                label = t("账号：{site} · {label}（房间「{room}」）", site=a.site, label=a.label, room=card_title(cfg, p))
                self.items[label] = (p, account_urls(a), f"{a.site} · {a.label}", a.site)
                preset_label = label if a == preset else preset_label
        for p in launcher.rooms:
            home = cfg.cards[p.card_id].home if p.card_id in cfg.cards else ""
            label = t("房间：{room}（{browser}）", room=card_title(cfg, p), browser=p.browser_label)
            self.items[label] = (p, [normalize(home)] if home else [], card_title(cfg, p), "")
            preset_label = label if isinstance(preset, Profile) and p.card_id == preset.card_id else preset_label

        self.win, f = _dialog(parent, t("创建快捷方式"))
        ttk.Label(f, text=t("启动项")).grid(row=0, column=0, sticky="w", pady=4)
        self.item = tk.StringVar(value=preset_label or next(iter(self.items), ""))
        box = ttk.Combobox(f, textvariable=self.item, values=list(self.items), state="readonly", width=46)
        box.grid(row=0, column=1, sticky="we", pady=4)
        box.bind("<<ComboboxSelected>>", lambda e: self._on_item())
        ttk.Label(f, text=t("名称")).grid(row=1, column=0, sticky="w", pady=4)
        self.name = tk.StringVar()
        ttk.Entry(f, textvariable=self.name, width=48).grid(row=1, column=1, sticky="we", pady=4)
        self.opens = ttk.Label(f, style="Muted.TLabel", wraplength=440, justify="left")
        self.opens.grid(row=2, column=1, sticky="w")
        ttk.Label(f, text=t("生成在")).grid(row=3, column=0, sticky="w", pady=(10, 4))
        where = ttk.Frame(f)
        where.grid(row=3, column=1, sticky="w", pady=(10, 4))
        self.where = {k: tk.BooleanVar(value=k == "desktop") for k in shortcuts.LOCATIONS}
        for k, text in shortcuts.LOCATIONS.items():
            ttk.Checkbutton(where, text=t(text), variable=self.where[k]).pack(side="left", padx=(0, 12))
        buttons = ttk.Frame(f)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(12, 0))
        ttk.Button(buttons, text=t("创建"), command=self.create).pack(side="right")
        ttk.Button(buttons, text=t("取消"), command=self.win.destroy).pack(side="right", padx=6)
        self._on_item()

    def _on_item(self) -> None:
        if self.item.get() not in self.items:
            return
        _, urls, name, _ = self.items[self.item.get()]
        self.name.set(name)
        self.opens.config(text=t("会打开：{urls}", urls=join_list(urls)) if urls else t("只打开这个房间"))

    def create(self) -> None:
        if self.item.get() not in self.items:
            return
        p, urls, _, site = self.items[self.item.get()]
        chosen = [k for k, v in self.where.items() if v.get()]
        if not chosen:
            messagebox.showwarning(t("创建快捷方式"), t("请选择生成在哪里。"), parent=self.win)
            return
        icon = shortcuts.site_ico(site) if site else None
        name = self.name.get().strip() or t("快捷方式")
        try:
            for where in chosen:
                shortcuts.create(name, p, urls, where, icon, "Profile Router")
        except OSError as e:
            messagebox.showerror(t("创建快捷方式"), str(e), parent=self.win)
            return
        self.win.destroy()
        self.launcher.status.config(text=t("已创建快捷方式「{name}」：{places}", name=name, places=join_list(
            t(shortcuts.LOCATIONS[k]) for k in chosen)))


class RoomDialog:
    """Room settings: name, start page, color, and the accounts registered in it (deletable here, so a room
    can be emptied and then deleted)."""

    def __init__(self, parent: tk.Misc, launcher: LauncherApp, p: Profile):
        self.launcher, self.p = launcher, p
        self.cfg = launcher.cfg
        c = self.cfg.card(p.card_id)
        self.win, f = _dialog(parent, t("房间设置"))
        ttk.Label(f, text=f"{p.browser_label} · {p.profile_id}", style="Muted.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(f, text=t("房间名")).grid(row=1, column=0, sticky="w", pady=6)
        self.name = tk.StringVar(value=c.name or p.name)
        ttk.Entry(f, textvariable=self.name, width=32).grid(row=1, column=1, columnspan=2, sticky="we")
        ttk.Label(f, text=t("打开时的网址")).grid(row=2, column=0, sticky="w", pady=6)
        self.home = tk.StringVar(value=c.home)
        ttk.Entry(f, textvariable=self.home, width=32).grid(row=2, column=1, columnspan=2, sticky="we")
        ttk.Label(f, text=t("颜色")).grid(row=3, column=0, sticky="w", pady=6)
        self.color = launcher.color_of(p.card_id)
        self.swatch = tk.Label(f, bg=self.color, width=4)
        self.swatch.grid(row=3, column=1, sticky="w")
        ttk.Button(f, text=t("选择…"), command=self.pick_color).grid(row=3, column=2, sticky="w")
        ttk.Label(f, text=t("这个房间里的账号"), style="Head.TLabel").grid(row=4, column=0, columnspan=3, sticky="w",
                                                                    pady=(14, 2))
        self.accounts = ttk.Frame(f)
        self.accounts.grid(row=5, column=0, columnspan=3, sticky="we")
        ttk.Button(f, text=t("保存"), command=self.save).grid(row=6, column=2, sticky="e", pady=(12, 0))
        self._fill_accounts()

    def _fill_accounts(self) -> None:
        for w in self.accounts.winfo_children():
            w.destroy()
        accts = [a for a in self.launcher.cfg.accounts if a.card == self.p.card_id]
        if not accts:
            ttk.Label(self.accounts, text=t("没有账号。现在可以在「房间」页的「⋯」里删除这个房间（主房间除外）。"),
                      style="Muted.TLabel", wraplength=420).pack(anchor="w")
        for a in accts:
            row = ttk.Frame(self.accounts)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"{a.site} · {a.label}").pack(side="left")
            ttk.Button(row, text=t("删除…"), command=lambda a=a: self.launcher.delete_account(
                a, after=self._after_delete)).pack(side="right")

    def _after_delete(self) -> None:
        if self.win.winfo_exists():
            self._fill_accounts()

    def pick_color(self) -> None:
        got = colorchooser.askcolor(self.color, parent=self.win)[1]
        if got:
            self.color = got
            self.swatch.config(bg=got)

    def save(self) -> None:
        cfg = self.launcher.cfg
        c = cfg.card(self.p.card_id)
        c.name = self.name.get().strip() if self.name.get().strip() != self.p.name else ""
        c.home = self.home.get().strip()
        c.color = self.color
        cfg.save()
        self.win.destroy()
        self.launcher.refresh()


class DeleteAccountsDialog:
    """Delete accounts. By default this also logs their rooms out of the site: the site's cookies, stored data
    and permissions in that room are removed for good (the user is warned). Needs the browser closed; otherwise
    the browser's own site-settings page can be opened to delete the data there."""

    def __init__(self, parent: tk.Misc, cfg: Config, profiles: list[Profile], accounts: list[Account], on_done,
                 remove_site: str = ""):
        self.cfg, self.accounts, self.on_done, self.remove_site = cfg, accounts, on_done, remove_site
        self.rooms = {p.card_id: p for p in profiles}
        title = t("移除网站 {site}", site=remove_site) if remove_site else \
            t("删除账号 {site} · {label}", site=accounts[0].site, label=accounts[0].label)
        self.win, f = _dialog(parent, title)
        ttk.Label(f, text=title, style="Head.TLabel").pack(anchor="w")
        lines = [t("· {site} · {label}（房间「{room}」）", site=a.site, label=a.label, room=self._room_name(a))
                 for a in accounts]
        ttk.Label(f, text=t("要删除的账号：\n{lines}", lines="\n".join(lines)), justify="left").pack(anchor="w", pady=(8, 6))
        warn = tk.Label(f, bg="#FFF4E5", fg="#8A4B00", font=(FONT, 10), justify="left", wraplength=480, padx=10,
                        pady=8, text=t("⚠ 删除账号会同时删除这个网站在该房间里的登录 Cookie、网站数据和权限设置，"
                                       "这个房间会退出该账号，无法恢复。下次要用得重新登录。"))
        warn.pack(fill="x")
        self.clear = tk.BooleanVar(value=True)
        ttk.Checkbutton(f, text=t("清除登录 Cookie 和网站数据（取消勾选则只删登记，浏览器里保持登录）"),
                        variable=self.clear).pack(anchor="w", pady=(8, 0))
        buttons = ttk.Frame(f)
        buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(buttons, text=t("删除"), command=self.submit).pack(side="right")
        ttk.Button(buttons, text=t("取消"), command=self.win.destroy).pack(side="right", padx=6)
        if len(accounts) == 1 and self.rooms.get(accounts[0].card, None) and \
                self.rooms[accounts[0].card].kind == "chromium":
            ttk.Button(buttons, text=t("在浏览器里删…"), command=self.open_site_settings).pack(side="left")

    def _room_name(self, a: Account) -> str:
        p = self.rooms.get(a.card)
        return card_title(self.cfg, p) if p else t("（找不到）")

    def open_site_settings(self) -> None:
        # Browsers refuse chrome:// pages passed on the command line, so open the room and copy the address.
        a = self.accounts[0]
        p = self.rooms[a.card]
        url = browsers.site_settings_url(p, a.site)
        self.win.clipboard_clear()
        self.win.clipboard_append(url)
        browsers.launch(p)
        messagebox.showinfo(t("网站设置"), t("已打开房间「{room}」，并复制了 {site} 的网站设置页地址。\n\n"
                                           "在地址栏粘贴（Ctrl+V）回车，点「删除数据」即可退出登录。\n"
                                           "删完回来点「删除」，并取消勾选清除（已经清过了）。",
                                           room=card_title(self.cfg, p), site=a.site), parent=self.win)

    def submit(self) -> None:
        targets = [(self.rooms[a.card], a) for a in self.accounts if a.card in self.rooms]
        if self.clear.get():
            busy = sorted({p.browser_label for p, _ in targets if p.kind == "chromium" and browsers.is_running(p.exe)})
            if busy:
                messagebox.showinfo(t("删除账号"), t("请先关闭 {browsers} 的所有窗口再删除——浏览器开着时登录数据被占用，"
                                                   "删不掉。\n也可以点「在浏览器里删…」，在浏览器的网站设置页里删。",
                                                   browsers=join_list(busy)), parent=self.win)
                return
        cleared = 0
        if self.clear.get():
            for p, a in targets:
                if p.kind == "chromium":
                    try:
                        cleared += browsers.clear_site_data(p, a.site)["cookies"]
                    except (OSError, sqlite3.Error) as e:
                        messagebox.showerror(t("删除账号"), t("清除 {site} 的数据时出错：{error}", site=a.site, error=e),
                                             parent=self.win)
                        return
        self.cfg.accounts = [x for x in self.cfg.accounts if x not in self.accounts]
        if self.remove_site:
            self.cfg.sites = [s for s in self.cfg.sites if s != self.remove_site]
        self.cfg.save()
        self.win.destroy()
        names = join_list(f"{a.site} · {a.label}" for a in self.accounts)
        self.on_done(t("已删除 {names}，清除了 {n} 个 Cookie", names=names, n=cleared) if self.clear.get()
                     else t("已删除 {names}（浏览器里仍保持登录）", names=names))


def _room_labels(cfg: Config, rooms: list[Profile]) -> dict[str, str]:
    return {p.card_id: room_label(cfg, p) for p in rooms}


class SettingsDialog:
    """Rare settings: how links open, default extensions for new rooms, and where things are stored."""

    def __init__(self, parent: tk.Misc, cfg: Config, rooms: list[Profile], on_saved, on_sync=None,
                 on_language=None):
        self.cfg, self.rooms, self.on_saved, self.on_language = cfg, rooms, on_saved, on_language
        self.labels = _room_labels(cfg, rooms)
        self.win, f = _dialog(parent, t("设置"))
        tabs = ttk.Notebook(f)
        tabs.pack(fill="both", expand=True)

        lang = ttk.Frame(tabs, padding=12)
        tabs.add(lang, text=t("语言"))
        self.languages = {"auto": t("跟随系统（{name}）", name=i18n.LANGUAGES[i18n.system_language()]),
                          **i18n.LANGUAGES}
        row = ttk.Frame(lang)
        row.pack(anchor="w")
        ttk.Label(row, text=t("界面语言")).pack(side="left")
        self.language = tk.StringVar(value=self.languages.get(cfg.language, self.languages["auto"]))
        ttk.Combobox(row, textvariable=self.language, values=list(self.languages.values()), state="readonly",
                     width=24).pack(side="left", padx=6)

        sync = ttk.Frame(tabs, padding=12)
        tabs.add(sync, text=t("同步"))
        self.auto_sync = tk.BooleanVar(value=cfg.auto_sync)
        ttk.Checkbutton(sync, text=t("自动同步：浏览器里新建、删除、改名的用户，不用重启就会出现在「房间」里"),
                        variable=self.auto_sync).pack(anchor="w")
        ttk.Button(sync, text=t("立即同步"), command=on_sync or on_saved).pack(anchor="w", pady=(8, 12))
        ttk.Label(sync, text=t("说明：网站账号要在「账号」页登记（＋），程序不会读取浏览器里的登录信息。"),
                  style="Muted.TLabel", wraplength=460).pack(anchor="w")

        links = ttk.Frame(tabs, padding=12)
        tabs.add(links, text=t("链接"))
        ttk.Label(links, text=t("设为默认浏览器后，从别的软件点开的链接也会送到对的账号。"), style="Muted.TLabel").pack(anchor="w")
        ttk.Button(links, text=t("设为默认浏览器…"), command=self.set_default).pack(anchor="w", pady=(4, 12))
        ttk.Label(links, text=t("打开没有登记账号的网站时：")).pack(anchor="w")
        self.ask = tk.BooleanVar(value=cfg.ask_unmatched)
        ttk.Radiobutton(links, text=t("弹窗让我选房间"), value=True, variable=self.ask).pack(anchor="w")
        row = ttk.Frame(links)
        row.pack(anchor="w")
        ttk.Radiobutton(row, text=t("总是用"), value=False, variable=self.ask).pack(side="left")
        self.fallback = tk.StringVar(value=self.labels.get(cfg.fallback, ""))
        ttk.Combobox(row, textvariable=self.fallback, values=list(self.labels.values()), state="readonly",
                     width=26).pack(side="left", padx=6)
        ttk.Button(links, text=t("按域名指定房间（规则）…"),
                   command=lambda: RulesDialog(self.win, cfg, rooms, on_saved=on_saved)).pack(anchor="w", pady=(12, 0))

        exts = ttk.Frame(tabs, padding=12)
        tabs.add(exts, text=t("新房间默认扩展"))
        ttk.Label(exts, text=t("新建房间时默认勾选这些扩展。"), style="Muted.TLabel").pack(anchor="w", pady=(0, 6))
        self.picker = ExtensionPicker(exts, cfg, rooms)
        self.picker.pack(fill="both", expand=True)

        about = ttk.Frame(tabs, padding=12)
        tabs.add(about, text=t("关于"))
        ttk.Label(about, text=f"Profile Router {__version__}").pack(anchor="w")
        ttk.Label(about, text=t("设置和图标保存在：{path}", path=config_path().parent), style="Muted.TLabel",
                  wraplength=460).pack(anchor="w", pady=4)
        ttk.Button(about, text=t("打开文件夹"), command=self.open_folder).pack(anchor="w")

        ttk.Button(f, text=t("保存"), command=self.save).pack(anchor="e", pady=(12, 0))

    def set_default(self) -> None:
        if not messagebox.askyesno(
            t("设为默认浏览器"),
            t("将在当前 Windows 用户下登记「Profile Router」为可选浏览器（只写 HKCU，可随时撤销）。\n\n"
              "登记后会打开 Windows 的「默认应用」设置，请在那里把 HTTP 和 HTTPS 改成 Profile Router。\n\n继续吗？"),
            parent=self.win,
        ):
            return
        register.register()
        os.startfile("ms-settings:defaultapps?registeredAppUser=ProfileRouter")

    def open_folder(self) -> None:
        path = config_path().parent
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(path)

    def save(self) -> None:
        self.cfg.auto_sync = self.auto_sync.get()
        self.cfg.ask_unmatched = self.ask.get()
        self.cfg.fallback = next((k for k, v in self.labels.items() if v == self.fallback.get()), "")
        self.cfg.new_profile_extensions = [e.id for e in self.picker.selected()]
        language = next((k for k, v in self.languages.items() if v == self.language.get()), "auto")
        changed = language != self.cfg.language
        self.cfg.language = language
        self.cfg.save()
        self.win.destroy()
        if changed:
            i18n.set_language(language)
            if self.on_language:
                self.on_language()
                return
            messagebox.showinfo(t("语言"), t("新的界面语言会在重新打开程序后生效。"))
        self.on_saved()


class RulesDialog:
    def __init__(self, parent: tk.Misc, cfg: Config, rooms: list[Profile], on_saved):
        self.cfg, self.on_saved = cfg, on_saved
        self.labels = _room_labels(cfg, rooms)
        self.win, f = _dialog(parent, t("按域名指定房间"))
        ttk.Label(f, text=t("网站没有登记账号时，按这里的规则选房间。github.com 也会匹配 gist.github.com；可以用 * 通配。"),
                  style="Muted.TLabel", wraplength=460).pack(anchor="w")
        self.tree = ttk.Treeview(f, columns=("pattern", "card"), show="headings", height=8)
        self.tree.heading("pattern", text=t("域名"))
        self.tree.heading("card", text=t("房间"))
        self.tree.column("pattern", width=200)
        self.tree.column("card", width=260)
        self.tree.pack(fill="both", expand=True, pady=8)
        add = ttk.Frame(f)
        add.pack(fill="x")
        self.pattern = tk.StringVar()
        ttk.Entry(add, textvariable=self.pattern, width=22).pack(side="left")
        self.card = tk.StringVar()
        ttk.Combobox(add, textvariable=self.card, values=list(self.labels.values()), state="readonly",
                     width=30).pack(side="left", padx=6)
        ttk.Button(add, text=t("添加"), command=self.add).pack(side="left")
        ttk.Button(add, text=t("删除选中"), command=self.remove).pack(side="left", padx=6)
        ttk.Button(f, text=t("保存"), command=self.save).pack(anchor="e", pady=(12, 0))
        self.rules = list(cfg.rules)
        self.fill()

    def fill(self) -> None:
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(self.rules):
            self.tree.insert("", "end", iid=str(i), values=(r.pattern, self.labels.get(r.card, t("{card}（未找到）", card=r.card))))

    def add(self) -> None:
        pattern = self.pattern.get().strip().lower()
        card = next((k for k, v in self.labels.items() if v == self.card.get()), "")
        if not pattern or not card:
            return
        host = host_of(pattern) if "/" in pattern else pattern
        self.rules = [r for r in self.rules if r.pattern != host] + [Rule(host, card)]
        self.pattern.set("")
        self.fill()

    def remove(self) -> None:
        drop = {int(i) for i in self.tree.selection()}
        self.rules = [r for i, r in enumerate(self.rules) if i not in drop]
        self.fill()

    def save(self) -> None:
        self.cfg.rules = self.rules
        self.cfg.save()
        self.win.destroy()
        self.on_saved()


class Picker:
    """Choose where one link opens; for plain rooms, optionally remember the choice as a rule for its domain."""

    def __init__(self, win: tk.Toplevel | tk.Tk, url: str, cfg: Config, choices: list[Choice], rememberable: bool,
                 on_done=None):
        self.win, self.url, self.cfg, self.on_done = win, url, cfg, on_done
        win.title(t("用哪个房间打开？") if rememberable else t("用哪个账号打开？"))
        win.configure(bg=BG)
        win.attributes("-topmost", True)
        f = ttk.Frame(win, padding=16)
        f.pack(fill="both")
        ttk.Label(f, text=url if len(url) <= 70 else url[:67] + "…", style="Muted.TLabel").pack(anchor="w")
        host = host_of(url)
        self.remember = tk.BooleanVar(value=False)
        if rememberable and host:
            ttk.Checkbutton(f, text=t("以后 {host} 都用这个房间打开", host=host), variable=self.remember).pack(anchor="w", pady=(6, 8))
        else:
            ttk.Label(f, text=t("这个网站登记了多个账号："), style="Muted.TLabel").pack(anchor="w", pady=(6, 8))
        for n, c in enumerate(choices, 1):
            b = tk.Button(f, text=f"{n}.  {c.title}    {c.subtitle}", anchor="w", relief="flat", bg=CARD_BG,
                          activebackground="#EEF1F6", font=(FONT, 10), padx=12, pady=6, highlightthickness=0, bd=0,
                          command=lambda c=c: self.choose(c.profile, host))
            b.pack(fill="x", pady=2)
            tk.Frame(b, bg=c.color, width=4).place(x=0, y=0, relheight=1)
            if n <= 9:
                win.bind(str(n), lambda e, c=c: self.choose(c.profile, host))
        win.bind("<Escape>", lambda e: win.destroy())

    def choose(self, p: Profile, host: str) -> None:
        if self.remember.get() and host:
            self.cfg.rules = [r for r in self.cfg.rules if r.pattern != host] + [Rule(host, p.card_id)]
            self.cfg.save()
        open_in(self.cfg, p, self.url)
        self.win.destroy()
        if self.on_done:
            self.on_done()


def handle_link(url: str) -> None:
    """Entry when Windows hands us a link (we are the default browser)."""
    cfg = Config.load()
    i18n.set_language(cfg.language)
    rooms = [p for p in browsers.all_profiles(cfg.extra_profiles) if p.card_id not in cfg.hidden_rooms]
    url = normalize(url)
    p, choices, remember = decide(url, cfg, rooms)
    if p:
        open_in(cfg, p, url)
        return
    root = tk.Tk()
    _style(root)
    Picker(root, url, cfg, choices, remember)
    root.mainloop()


def run_launcher() -> None:
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, OSError, AttributeError):
        pass
    i18n.set_language(Config.load().language)
    root = tk.Tk()
    LauncherApp(root)
    root.mainloop()
