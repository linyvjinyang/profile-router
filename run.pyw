"""Windowless entry point: double-click to open the launcher; Windows passes a URL when this is the default browser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from profile_router.__main__ import main  # noqa: E402

main(sys.argv[1:])
