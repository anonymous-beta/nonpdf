"""Payload modules register themselves with nonpdf.core.registry.registry
at import time. Importing this package pulls every module in."""
from nonpdf.payloads import (  # noqa: F401
    actions,
    browser,
    embedded,
    fonts,
    javascript,
    unc,
    xfa,
    xxe,
)
