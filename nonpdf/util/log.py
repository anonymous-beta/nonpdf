from __future__ import annotations

import logging
import sys


def configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    root = logging.getLogger("nonpdf")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
