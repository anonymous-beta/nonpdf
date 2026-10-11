"""Shared state for the TUI.

Everything that survives screen switches lives here. Screens read/write
through ``self.app.state``.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TuiState:
    callback: str = ""
    output_dir: str = "output"
    profile: str = "full"
    obfuscate: int = 0
    recent_builds: list[tuple[str, str]] = field(default_factory=list)
    hits: list[tuple[str, str, str, str]] = field(default_factory=list)
    # ^ (timestamp, method, ip, path)

    def add_build(self, path: str, desc: str) -> None:
        self.recent_builds.insert(0, (path, desc))
        del self.recent_builds[50:]

    def add_hit(self, ts: str, method: str, ip: str, path: str) -> None:
        self.hits.insert(0, (ts, method, ip, path))
        del self.hits[500:]