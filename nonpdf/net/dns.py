"""DNS callback listener.

Minimal UDP + TCP DNS responder. Answers every A query with the listener
host's IP (default 127.0.0.1) and fires an on_hit callback with the parsed
qname so the correlator can map the subdomain back to a payload.

Implements just enough of RFC 1035 to satisfy typical resolvers. No
recursion, no caching — every query is a fresh callback observation.
"""
from __future__ import annotations

import socket
import struct
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Callable


@dataclass
class DnsHit:
    timestamp: str
    qname: str
    qtype: int
    client_ip: str
    transport: str  # "udp" | "tcp"

    def payload_id(self) -> str:
        # The correlator resolves the full mapping; this is just the label
        # the TUI uses as a fallback when no correlation was recorded.
        segs = self.qname.rstrip(".").split(".")
        return segs[0] if segs else "-"


_QTYPE_NAMES = {1: "A", 28: "AAAA", 5: "CNAME", 16: "TXT", 15: "MX", 2: "NS"}


def qtype_name(qtype: int) -> str:
    return _QTYPE_NAMES.get(qtype, str(qtype))


class DnsServer:
    """UDP + TCP DNS responder with callback hooks."""

    def __init__(self, host: str = "0.0.0.0", port: int = 53,
                 answer_ip: str = "127.0.0.1",
                 on_hit: Callable[[DnsHit], None] | None = None) -> None:
        self.host = host
        self.port = port
        self.answer_ip = answer_ip
        self.on_hit = on_hit
        self._udp_sock: socket.socket | None = None
        self._tcp_sock: socket.socket | None = None
        self._udp_thread: threading.Thread | None = None
        self._tcp_thread: threading.Thread | None = None
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        if self._running:
            return
        self._udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._udp_sock.bind((self.host, self.port))

        self._tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._tcp_sock.bind((self.host, self.port))
        self._tcp_sock.listen(16)

        self._running = True
        self._udp_thread = threading.Thread(
            target=self._udp_loop, daemon=True, name="nonpdf-dns-udp",
        )
        self._tcp_thread = threading.Thread(
            target=self._tcp_loop, daemon=True, name="nonpdf-dns-tcp",
        )
        self._udp_thread.start()
        self._tcp_thread.start()

    def stop(self) -> None:
        self._running = False
        for s in (self._udp_sock, self._tcp_sock):
            if s is not None:
                try:
                    s.close()
                except Exception:
                    pass
        self._udp_sock = None
        self._tcp_sock = None

    # ---- wire helpers -------------------------------------------------

    @staticmethod
    def _parse_question(data: bytes) -> tuple[str, int] | None:
        """Return (qname, qtype) from a DNS query packet, or None if malformed."""
        if len(data) < 12:
            return None
        # skip header (12 bytes) + parse qname
        i = 12
        labels = []
        while i < len(data):
            ln = data[i]
            if ln == 0:
                i += 1
                break
            if ln & 0xC0:
                # compression pointer — not expected in a query's qname
                return None
            i += 1
            if i + ln > len(data):
                return None
            labels.append(data[i:i + ln].decode("latin-1", errors="replace"))
            i += ln
        if i + 4 > len(data):
            return None
        qtype = struct.unpack("!H", data[i:i + 2])[0]
        return ".".join(labels), qtype

    def _build_response(self, query: bytes, qname: str, qtype: int) -> bytes:
        """Build a minimal A record response, echoing the question."""
        tid = query[:2]
        # flags: QR=1, RD=1, RA=1, RCODE=0
        flags = b"\x81\x80"
        qdcount = b"\x00\x01"
        ancount = b"\x00\x01" if qtype in (1, 255) else b"\x00\x00"
        nscount = b"\x00\x00"
        arcount = b"\x00\x00"
        header = tid + flags + qdcount + ancount + nscount + arcount

        # qname on the wire
        qwire = b""
        for label in qname.split("."):
            if not label:
                continue
            qwire += bytes([len(label)]) + label.encode("latin-1")
        qwire += b"\x00"
        qtail = struct.pack("!HH", qtype, 1)
        question = qwire + qtail

        answer = b""
        if qtype in (1, 255):
            # pointer to qname at offset 12
            answer = (
                b"\xc0\x0c"
                + struct.pack("!HH", 1, 1)   # type A, class IN
                + struct.pack("!I", 60)      # TTL 60s
                + struct.pack("!H", 4)       # rdlength
                + socket.inet_aton(self.answer_ip)
            )
        return header + question + answer

    def _fire(self, qname: str, qtype: int, client_ip: str, transport: str) -> None:
        if self.on_hit is None:
            return
        hit = DnsHit(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            qname=qname, qtype=qtype, client_ip=client_ip, transport=transport,
        )
        try:
            self.on_hit(hit)
        except Exception:
            pass

    # ---- loops --------------------------------------------------------

    def _udp_loop(self) -> None:
        sock = self._udp_sock
        if sock is None:
            return
        while self._running:
            try:
                data, addr = sock.recvfrom(512)
            except OSError:
                break
            parsed = self._parse_question(data)
            if not parsed:
                continue
            qname, qtype = parsed
            self._fire(qname, qtype, addr[0], "udp")
            try:
                sock.sendto(self._build_response(data, qname, qtype), addr)
            except OSError:
                pass

    def _tcp_loop(self) -> None:
        sock = self._tcp_sock
        if sock is None:
            return
        while self._running:
            try:
                conn, addr = sock.accept()
            except OSError:
                break
            threading.Thread(
                target=self._tcp_handle, args=(conn, addr),
                daemon=True, name="nonpdf-dns-tcp-conn",
            ).start()

    def _tcp_handle(self, conn: socket.socket, addr) -> None:
        try:
            # 2-byte length prefix
            hdr = conn.recv(2)
            if len(hdr) < 2:
                return
            ln = struct.unpack("!H", hdr)[0]
            data = b""
            while len(data) < ln:
                chunk = conn.recv(ln - len(data))
                if not chunk:
                    break
                data += chunk
            parsed = self._parse_question(data)
            if not parsed:
                return
            qname, qtype = parsed
            self._fire(qname, qtype, addr[0], "tcp")
            resp = self._build_response(data, qname, qtype)
            conn.sendall(struct.pack("!H", len(resp)) + resp)
        except OSError:
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass