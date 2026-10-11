"""Anonymous-beta (chinedu) branding for generated artifacts.

Every PDF we produce carries a consistent metadata signature so engagement
output is attributable to the operator's org, not to any upstream source.
"""
from __future__ import annotations

BRAND = "Anonymous-beta"
CREATOR_NAME = "Anonymous-beta (chinedu)"
PRODUCER = "NonPDF"
CREATOR = CREATOR_NAME

PDF_HEADER_COMMENT = (
    f"% NonPDF — {BRAND} — Creator: {CREATOR_NAME}\n".encode()
)
INFO_DICT = (
    f" /Info << /Creator ({CREATOR}) /Producer ({PRODUCER} by {BRAND})"
    f" /Title (NonPDF) /Author ({CREATOR_NAME}) >>"
).encode()
FOOTER_TEXT = f"NonPDF · {CREATOR_NAME}"