"""Interactsh-style correlator.

Each payload build mints a unique subdomain under the operator's callback
domain (or reuses the operator's URL with a uniquified path). When a hit
arrives (HTTP or DNS), the correlator maps the incoming host/path back to
the payload ID that generated it, so the TUI can jump straight to the
vector that fired.

Modes:
  • url        — callback is a full URL; we append /<corr-id>
  • domain     — callback is a bare domain; we prepend <corr-id>.<domain>
  • auto       — pick based on whether the callback looks like a URL or not
"""
from __future__ import annotations

import secrets
import string
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlparse

_ALPHABET = string.ascii_lowercase + string.digits


@dataclass
class Correlation:
    corr_id: str
    payload_id: str
    payload_name: str
    callback_url: str
    domain: str
    created: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))


class Correlator:
    def __init__(self, callback: str, mode: str = "auto") -> None:
        self.callback = callback.strip()
        self.mode = mode
        self._by_id: dict[str, Correlation] = {}
        self._by_domain: dict[str, Correlation] = {}
        self._by_path: dict[str, Correlation] = {}

        parsed = urlparse(self.callback)
        if parsed.scheme in ("http", "https"):
            self._scheme = parsed.scheme
            self._host = parsed.netloc or parsed.path
            self._base_path = (parsed.path or "").rstrip("/")
            self._is_url = True
        else:
            self._scheme = "http"
            self._host = self.callback.split("/")[0]
            self._base_path = ""
            self._is_url = False

        if mode == "auto":
            self.mode = "url" if self._is_url else "domain"

    # ---- minting ------------------------------------------------------

    def mint(self, payload_id: str, payload_name: str) -> Correlation:
        cid = self._new_id()
        if self.mode == "url":
            url = f"{self._scheme}://{self._host}{self._base_path}/{cid}"
            domain = f"{cid}.{self._host}"
            corr = Correlation(
                corr_id=cid, payload_id=payload_id, payload_name=payload_name,
                callback_url=url, domain=domain,
            )
            self._by_path[cid] = corr
        else:
            domain = f"{cid}.{self._host}"
            url = f"{self._scheme}://{domain}"
            corr = Correlation(
                corr_id=cid, payload_id=payload_id, payload_name=payload_name,
                callback_url=url, domain=domain,
            )
            self._by_domain[domain.lower()] = corr
        self._by_id[cid] = corr
        return corr

    @staticmethod
    def _new_id(length: int = 10) -> str:
        return "".join(secrets.choice(_ALPHABET) for _ in range(length))

    # ---- resolution ---------------------------------------------------

    def resolve_http(self, path: str, host_header: str | None = None) -> Correlation | None:
        """Resolve an HTTP hit back to its correlation.

        Tries (in order): exact domain match from Host header, first path
        segment, then any corr_id substring in the full path.
        """
        if host_header:
            h = host_header.split(":")[0].lower()
            if h in self._by_domain:
                return self._by_domain[h]
        segs = [s for s in path.split("/") if s]
        for seg in segs:
            if seg in self._by_id:
                return self._by_id[seg]
            if seg in self._by_path:
                return self._by_path[seg]
        for cid, corr in self._by_id.items():
            if cid in path:
                return corr
        return None

    def resolve_dns(self, qname: str) -> Correlation | None:
        q = qname.rstrip(".").lower()
        if q in self._by_domain:
            return self._by_domain[q]
        for cid, corr in self._by_id.items():
            if cid in q:
                return corr
        return None

    # ---- introspection ------------------------------------------------

    def all(self) -> list[Correlation]:
        return sorted(self._by_id.values(), key=lambda c: c.created, reverse=True)

    def get(self, corr_id: str) -> Correlation | None:
        return self._by_id.get(corr_id)