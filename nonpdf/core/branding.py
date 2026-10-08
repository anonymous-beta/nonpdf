"""Anonymous-beta branding for generated artifacts.

Every PDF we produce carries a consistent metadata signature so engagement
output is attributable to the operator's org, not to any upstream source.
"""
from __future__ import annotations

BRAND = "Anonymous-beta"
PRODUCER = "NonPDF"
CREATOR = "NonPDF"

PDF_HEADER_COMMENT = f"% NonPDF - {BRAND} - https://github.com/anonymous-beta/nonpdf\n".encode()
INFO_DICT = (
    f" /Info << /Creator ({CREATOR}) /Producer ({PRODUCER} by {BRAND}) /Title (NonPDF) >>"
).encode()
FOOTER_TEXT = f"NonPDF by {BRAND}"
