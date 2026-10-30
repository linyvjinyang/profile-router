"""python -m profile_router [URL]

Without a URL: open the launcher. With a URL: route it by the rules (or ask), as the default browser does.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    from .app import handle_link, run_launcher

    if argv and argv[0] in ("--register", "--unregister"):
        from . import register

        register.register() if argv[0] == "--register" else register.unregister()
        print("done")
        return
    if argv:
        handle_link(argv[0])
    else:
        run_launcher()


if __name__ == "__main__":
    main()
