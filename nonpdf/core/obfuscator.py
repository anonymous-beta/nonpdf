"""Obfuscation engine.

Level 0: none
Level 1: PDF name hex-encoding + string octal/hex encoding
Level 2: + JS bracket notation + javascript: URI case variation
Level 3: + FlateDecode stream compression
Level 4: + JS payload staging (base64 / charcode decoder wrappers)
"""
from __future__ import annotations

import base64
import random
import re
import zlib
from pathlib import Path

_BROWSER_API_HINTS = (b'fetch(', b'XMLHttpRequest', b'new Image', b'WebSocket')

_KEYWORD_NAMES = [
    b'/JavaScript', b'/OpenAction', b'/Launch', b'/SubmitForm',
    b'/GoToR', b'/GoToE', b'/ImportData', b'/Thread',
    b'/RichMedia', b'/EmbeddedFile', b'/XFA', b'/OCProperties',
]


def name_to_hex(name: bytes) -> bytes:
    if not name.startswith(b'/'):
        return name
    out = b'/'
    for b in name[1:]:
        if random.random() < 0.7:
            out += b'#' + format(b, '02x').encode()
        else:
            out += bytes([b])
    return out


def _string_to_octal(match: re.Match[bytes]) -> bytes:
    content = match.group(1)
    out = b'('
    for b in content:
        if b in (0x28, 0x29, 0x5c):
            out += b'\\' + bytes([b])
        elif random.random() < 0.6:
            out += b'\\' + format(b, '03o').encode()
        else:
            out += bytes([b])
    out += b')'
    return out


def _string_to_hex(match: re.Match[bytes]) -> bytes:
    content = match.group(1)
    out = b'<'
    for b in content:
        out += format(b, '02x').encode()
        if random.random() < 0.3:
            out += b' '
    out += b'>'
    return out


def _obfuscate_js_uri(uri: bytes) -> bytes:
    if not uri.lower().startswith(b'javascript:'):
        return uri
    prefix = uri[:11]
    payload = uri[11:]
    obf = b''.join(
        bytes([c]).upper() if random.random() < 0.5 else bytes([c])
        for c in prefix[:-1]
    ) + b':'
    if random.random() < 0.5:
        pos = random.randint(1, max(1, len(obf) - 2))
        obf = obf[:pos] + random.choice([b'\t', b'\n']) + obf[pos:]
    return obf + payload


def _rewrite_js_blocks(data: bytes, transform) -> bytes:
    pattern = re.compile(rb'/JS\s*\(')
    out = bytearray()
    pos = 0
    while True:
        m = pattern.search(data, pos)
        if not m:
            out.extend(data[pos:])
            break
        out.extend(data[pos:m.end()])
        depth = 1
        i = m.end()
        while i < len(data) and depth > 0:
            c = data[i]
            if c == 0x5c:
                i += 2
                continue
            if c == 0x28:
                depth += 1
            elif c == 0x29:
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if depth != 0:
            out.extend(data[m.end():])
            return bytes(out)
        out.extend(transform(data[m.end():i]))
        out.extend(b')')
        pos = i + 1
    return bytes(out)


def _bracket_notation(js: bytes) -> bytes:
    s = js.decode('latin-1')
    reps = [
        ('this.submitForm', 'this["submitForm"]'),
        ('this.getURL', 'this["getURL"]'),
        ('this.importDataObject', 'this["importDataObject"]'),
        ('app.launchURL', 'app["launchURL"]'),
        ('app.openDoc', 'app["openDoc"]'),
        ('app.media.getURLData', 'app["media"]["getURLData"]'),
        ('app.setTimeOut', 'app["setTimeOut"]'),
        ('SOAP.connect', 'SOAP["connect"]'),
        ('SOAP.request', 'SOAP["request"]'),
        ('SOAP.streamDecode', 'SOAP["streamDecode"]'),
        ('RSS.addFeed', 'RSS["addFeed"]'),
        ('util.readFileIntoStream', 'util["readFileIntoStream"]'),
        ('util.stringFromStream', 'util["stringFromStream"]'),
        ('util.streamFromString', 'util["streamFromString"]'),
    ]
    for old, new in reps:
        s = s.replace(old, new)
    return s.encode('latin-1')


def _stage_charcode(js: bytes) -> bytes:
    codes = ','.join(str(b) for b in js)
    return f'eval(String.fromCharCode({codes}))'.encode()


def _stage_base64(js: bytes) -> bytes:
    b64 = base64.b64encode(js).decode('ascii')
    return (
        f'eval(util.stringFromStream('
        f'util.streamFromString("{b64}"),"base64"))'
    ).encode('latin-1')


def obfuscate_pdf(path: Path, level: int) -> None:
    if level <= 0:
        return
    data = path.read_bytes()
    if not data.startswith(b'%PDF'):
        return

    if level >= 4:
        def _stage(js: bytes) -> bytes:
            if any(h in js for h in _BROWSER_API_HINTS):
                return _stage_charcode(js)
            return _stage_base64(js)
        data = _rewrite_js_blocks(data, _stage)

    if level >= 2:
        data = _rewrite_js_blocks(data, _bracket_notation)
        data = re.sub(rb'javascript:[^\)"]+', lambda m: _obfuscate_js_uri(m.group(0)), data)

    if level >= 1:
        for kw in _KEYWORD_NAMES:
            if kw in data:
                data = data.replace(kw, name_to_hex(kw), 1)
        data = re.sub(rb'/JS\s*\(', lambda m: name_to_hex(b'/JS') + b' (', data)
        data = re.sub(rb'/AA\s*<', lambda m: name_to_hex(b'/AA') + b' <', data)

    if level >= 3:
        def _compress(m: re.Match[bytes]) -> bytes:
            d = m.group(1)
            s = m.group(2)
            if b'/Filter' in d or len(s) < 50:
                return m.group(0)
            try:
                comp = zlib.compress(s)
                nd = re.sub(rb'/Length\s+\d+', b'/Length ' + str(len(comp)).encode(), d)
                if b'/Length' not in nd:
                    nd = nd.rstrip(b' >') + b' /Length ' + str(len(comp)).encode()
                nd += b' /Filter /FlateDecode'
                return b'<< ' + nd + b' >>\nstream\n' + comp + b'\nendstream'
            except Exception:
                return m.group(0)
        data = re.sub(
            rb'<<\s*(.*?)\s*>>\s*stream\n(.*?)\nendstream',
            _compress, data, flags=re.DOTALL,
        )

    path.write_bytes(data)
