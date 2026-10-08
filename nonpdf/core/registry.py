from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable

PayloadFn = Callable[..., bytes]


@dataclass(frozen=True)
class PayloadEntry:
    id: str
    name: str
    builder: PayloadFn
    description: str
    platform: str = "acrobat"    # acrobat | pdfium | pdfjs | server | all
    cve: str | None = None
    tags: tuple[str, ...] = field(default_factory=tuple)
    needs_host: bool = True


class Registry:
    """Global payload registry. Payload modules register at import time."""

    _entries: dict[str, PayloadEntry] = {}

    def register(self, entry: PayloadEntry) -> PayloadEntry:
        self._entries[entry.id] = entry
        return entry

    def get(self, pid: str) -> PayloadEntry:
        return self._entries[pid]

    def all(self) -> list[PayloadEntry]:
        return sorted(self._entries.values(), key=lambda e: e.id)

    def filter(self, *, platform: str | None = None, tags: Iterable[str] | None = None,
               ids: Iterable[str] | None = None) -> list[PayloadEntry]:
        result = list(self._entries.values())
        if platform:
            result = [e for e in result if e.platform in (platform, "all")]
        if tags:
            tagset = set(tags)
            result = [e for e in result if tagset & set(e.tags)]
        if ids:
            idset = set(ids)
            result = [e for e in result if e.id in idset]
        return sorted(result, key=lambda e: e.id)


registry = Registry()
