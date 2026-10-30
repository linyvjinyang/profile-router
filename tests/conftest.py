import tkinter as tk

import pytest

from profile_router import i18n


@pytest.fixture(autouse=True)
def chinese_ui():
    """Tests assert the Chinese source texts, so pin the UI language regardless of the machine's locale."""
    i18n.set_language("zh")
    yield
    i18n.set_language("zh")


@pytest.fixture(scope="session")
def _tk():
    # One Tk interpreter for the whole run: creating and destroying many in one process makes Tcl
    # intermittently fail to find its own library files on Windows.
    try:
        r = tk.Tk()
    except tk.TclError as e:
        pytest.skip(f"no display: {e}")
    r.withdraw()
    yield r
    r.destroy()


@pytest.fixture
def root(_tk):
    """The shared Tk root, emptied after each test (widgets destroyed, pending timers cancelled)."""
    title = _tk.title()
    yield _tk
    for w in _tk.winfo_children():
        w.destroy()
    for job in _tk.tk.splitlist(_tk.tk.call("after", "info")):
        _tk.after_cancel(job)
    _tk.title(title)
