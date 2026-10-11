"""Shared state for the TUI.

Session object (correlator + listeners + store) is the single source of
truth for the active engagement. Screens read/write through ``app.state``.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from nonpdf.net.session import Session


@dataclass
class TuiState:
    callback: str = ""
    output_dir: str = "output"
    profile: str = "full"
    obfuscate: int = 0
    engagement: str = "default"
    recent_builds: list[tuple[str, str, str, str]] = field(default_factory=list)
    # ^ (path, desc, payload_id, corr_id)
    hits: list[tuple[str, str, str, str, str, str]] = field(default_factory=list)
    # ^ (ts, source, method, client, path, corr_id)

    def add_build(self, path: str, desc: str, payload_id: str, corr_id: str) -> None:
        self.recent_builds.insert(0, (path, desc, payload_id, corr_id))
        del self.recent_builds[200:]

    def add_hit(self, ts: str, source: str, method: str,
                client: str, path: str, corr_id: str) -> None:
        self.hits.insert(0, (ts, source, method, client, path, corr_id))
        del self.hits[1000:]