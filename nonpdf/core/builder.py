"""Low-level PDF structural helpers.

Payload builders compose these primitives. Keeps the payload modules
declarative and readable.
"""
from __future__ import annotations

from typing import Iterable


def pdf_header(version: str = "1.7", comment: bytes | None = None) -> bytes:
    head = f"%PDF-{version}\n".encode()
    if comment:
        head += comment
    return head


def obj(num: int, body: bytes | str) -> bytes:
    if isinstance(body, str):
        body = body.encode("latin-1")
    return f"{num} 0 obj\n".encode() + body + b"\nendobj\n"


def stream_obj(num: int, dict_body: bytes | str, stream: bytes) -> bytes:
    if isinstance(dict_body, str):
        dict_body = dict_body.encode("latin-1")
    head = f"{num} 0 obj\n".encode() + dict_body + b"\nstream\n"
    return head + stream + b"\nendstream\nendobj\n"


def trailer(root_obj: int, size: int, info_obj: int | None = None,
            extra: bytes | str = b"") -> bytes:
    if isinstance(extra, str):
        extra = extra.encode("latin-1")
    info = f" /Info {info_obj} 0 R".encode() if info_obj else b""
    return (
        b"trailer\n<< /Root " + f"{root_obj} 0 R".encode()
        + f" /Size {size}".encode() + info + extra + b" >>\n%%EOF\n"
    )


def join(parts: Iterable[bytes]) -> bytes:
    return b"".join(parts)


def obj_ref(n: int) -> bytes:
    return f"{n} 0 R".encode()
