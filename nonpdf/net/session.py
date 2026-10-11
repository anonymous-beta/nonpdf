"""Session — the runtime object tying correlator + listeners + store together.

The TUI holds exactly one Session for the active engagement. Everything
(callback server, DNS listener, correlator, store) lives inside it, so
starting/stopping is a single call.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from nonpdf.net.callback import CallbackServer, Hit as HttpHit
from nonpdf.net.correlator import Correlator
from nonpdf.net.dns import DnsServer, DnsHit
from nonpdf.net.store import EngagementStore


@dataclass
class SessionHit:
    """A unified hit record used by the TUI (HTTP or DNS)."""
    ts: str
    source: str          # "http" | "dns"
    method: str          # GET/POST/... or "A"/"AAAA"/...
    client: str
    path: str            # URL path (http) or qname (dns)
    corr_id: str
    payload_id: str
    payload_name: str
    description: str


class Session:
    def __init__(self, name: str, callback: str,
                 http_port: int = 8080, dns_port: int = 53,
                 dns_answer_ip: str = "127.0.0.1",
                 store_root: Path | None = None,
                 on_hit: Callable[[SessionHit], None] | None = None) -> None:
        self.name = name
        self.callback = callback
        self.http_port = http_port
        self.dns_port = dns_port
        self.dns_answer_ip = dns_answer_ip
        self.on_hit = on_hit

        self.correlator = Correlator(callback)
        self.store = EngagementStore(name, root=store_root)
        self.store.set_meta("name", name)
        self.store.set_meta("callback", callback)
        self.store.set_meta("created", datetime.now().isoformat(timespec="seconds"))

        self.http: CallbackServer | None = None
        self.dns: DnsServer | None = None

    # ---- correlation / build helpers ---------------------------------

    def mint_for(self, payload_id: str, payload_name: str):
        return self.correlator.mint(payload_id, payload_name)

    def record_build(self, *, payload_id: str, payload_name: str,
                     corr_id: str, callback_url: str, domain: str,
                     path: str, description: str = "",
                     obfuscate: int = 0) -> None:
        self.store.record_build(
            payload_id=payload_id, payload_name=payload_name,
            corr_id=corr_id, callback_url=callback_url, domain=domain,
            path=path, description=description, obfuscate=obfuscate,
        )

    # ---- listener lifecycle ------------------------------------------

    def start_http(self, port: int | None = None) -> int:
        port = port or self.http_port
        if self.http and self.http.running:
            return self.http.port

        def on_http(hit: HttpHit) -> None:
            self._handle_http(hit)

        self.http = CallbackServer(port=port, on_hit=on_http)
        self.http.start()
        self.http_port = port
        return port

    def stop_http(self) -> None:
        if self.http and self.http.running:
            self.http.stop()
        self.http = None

    def start_dns(self, port: int | None = None,
                  answer_ip: str | None = None) -> int:
        port = port or self.dns_port
        ip = answer_ip or self.dns_answer_ip
        if self.dns and self.dns.running:
            return self.dns.port

        def on_dns(hit: DnsHit) -> None:
            self._handle_dns(hit)

        self.dns = DnsServer(host="0.0.0.0", port=port,
                             answer_ip=ip, on_hit=on_dns)
        self.dns.start()
        self.dns_port = port
        self.dns_answer_ip = ip
        return port

    def stop_dns(self) -> None:
        if self.dns and self.dns.running:
            self.dns.stop()
        self.dns = None

    def stop_all(self) -> None:
        self.stop_http()
        self.stop_dns()

    def close(self) -> None:
        self.stop_all()
        self.store.close()

    # ---- hit handling -------------------------------------------------

    def _handle_http(self, hit: HttpHit) -> None:
        corr = self.correlator.resolve_http(
            path=hit.path,
            host_header=hit.headers.get("Host", ""),
        )
        corr_id = corr.corr_id if corr else ""
        payload_id = corr.payload_id if corr else ""
        payload_name = corr.payload_name if corr else ""
        desc = ""
        if payload_id:
            b = self.store.build_for_corr(corr_id)
            if b:
                desc = b.description

        self.store.record_hit(
            source="http", method=hit.method, client=hit.client_ip,
            path=hit.path, corr_id=corr_id, payload_id=payload_id,
            raw={"user_agent": hit.user_agent, "headers": hit.headers},
        )
        if self.on_hit is not None:
            self.on_hit(SessionHit(
                ts=hit.timestamp, source="http", method=hit.method,
                client=hit.client_ip, path=hit.path, corr_id=corr_id,
                payload_id=payload_id, payload_name=payload_name,
                description=desc,
            ))

    def _handle_dns(self, hit: DnsHit) -> None:
        from nonpdf.net.dns import qtype_name
        corr = self.correlator.resolve_dns(hit.qname)
        corr_id = corr.corr_id if corr else ""
        payload_id = corr.payload_id if corr else ""
        payload_name = corr.payload_name if corr else ""
        desc = ""
        if payload_id:
            b = self.store.build_for_corr(corr_id)
            if b:
                desc = b.description

        self.store.record_hit(
            source="dns", method=qtype_name(hit.qtype), client=hit.client_ip,
            path=hit.qname, corr_id=corr_id, payload_id=payload_id,
            raw={"transport": hit.transport, "qtype": hit.qtype},
        )
        if self.on_hit is not None:
            self.on_hit(SessionHit(
                ts=hit.timestamp, source="dns",
                method=qtype_name(hit.qtype), client=hit.client_ip,
                path=hit.qname, corr_id=corr_id, payload_id=payload_id,
                payload_name=payload_name, description=desc,
            ))