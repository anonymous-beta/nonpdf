"""HTTP callback server.

Threaded listener that writes a normalized Hit record for every request
it receives. The TUI consumes hits via an on_hit callback; the CLI uses
the same class in Wave 3 for headless operation.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Callable


@dataclass
class Hit:
    timestamp: str
    method: str
    path: str
    client_ip: str
    user_agent: str
    headers: dict[str, str] = field(default_factory=dict)

    def payload_id(self) -> str:
        """Best-effort extraction of the payload ID from the request path.

        NonPDF payload builders embed ``/p-<slug>`` / ``/j-<slug>`` /
        ``/x-<slug>`` / ``/m-<slug>`` / ``/b-<slug>`` markers. We surface the
        matched slug so the TUI can correlate hits back to the vector.
        """
        import re
        m = re.search(r"/([pjxmb]|u)-([a-z0-9_\-]+)", self.path, re.IGNORECASE)
        if m:
            return f"{m.group(1).upper()}:{m.group(2)}"
        # fall back: first non-empty path segment
        segs = [s for s in self.path.split("/") if s]
        return segs[0] if segs else "-"


class CallbackServer:
    """Threaded HTTP callback listener.

    Usage:
        srv = CallbackServer(port=8080, on_hit=print)
        srv.start()
        ...
        srv.stop()
    """

    def __init__(self, port: int = 8080,
                 on_hit: Callable[[Hit], None] | None = None) -> None:
        self.port = port
        self.on_hit = on_hit
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._httpd is not None

    def start(self) -> None:
        if self._httpd is not None:
            return
        on_hit = self.on_hit

        class _Handler(BaseHTTPRequestHandler):
            server_version = "NonPDF/0.1"

            def log_message(self, *args, **kwargs) -> None:  # silence stdout
                return

            def do_GET(self) -> None:   # noqa: N802
                self._handle("GET")

            def do_POST(self) -> None:  # noqa: N802
                self._handle("POST")

            def do_HEAD(self) -> None:  # noqa: N802
                self._handle("HEAD")

            def _handle(self, method: str) -> None:
                hit = Hit(
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    method=method,
                    path=self.path,
                    client_ip=self.client_address[0],
                    user_agent=self.headers.get("User-Agent", ""),
                    headers={k: v for k, v in self.headers.items()},
                )
                if on_hit is not None:
                    try:
                        on_hit(hit)
                    except Exception:
                        pass
                # always answer 200 so payloads complete cleanly
                self.send_response(200)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(b"nonpdf:ok")

        self._httpd = ThreadingHTTPServer(("0.0.0.0", self.port), _Handler)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True, name="nonpdf-http",
        )
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is None:
            return
        try:
            self._httpd.shutdown()
            self._httpd.server_close()
        finally:
            self._httpd = None
            self._thread = None