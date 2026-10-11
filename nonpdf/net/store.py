"""Per-engagement persistence.

Each engagement is a SQLite database stored under ``~/.nonpdf/engagements/``.
The store records:
  • engagement metadata (name, callback, created)
  • payload builds (payload_id, name, path, corr_id, callback_url, timestamp)
  • hits (timestamp, source, method, client, path, corr_id, payload_id)

The TUI reads from the same store for the activity feed and click-through.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator


DEFAULT_ROOT = Path.home() / ".nonpdf" / "engagements"


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS builds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    payload_id TEXT NOT NULL,
    payload_name TEXT NOT NULL,
    corr_id TEXT NOT NULL,
    callback_url TEXT NOT NULL,
    domain TEXT NOT NULL,
    path TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    obfuscate INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    source TEXT NOT NULL,          -- http | dns
    method TEXT NOT NULL,
    client TEXT NOT NULL,
    path TEXT NOT NULL,
    corr_id TEXT NOT NULL DEFAULT '',
    payload_id TEXT NOT NULL DEFAULT '',
    raw TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_hits_corr ON hits(corr_id);
CREATE INDEX IF NOT EXISTS idx_hits_payload ON hits(payload_id);
CREATE INDEX IF NOT EXISTS idx_builds_corr ON builds(corr_id);
CREATE INDEX IF NOT EXISTS idx_builds_payload ON builds(payload_id);
"""


@dataclass
class BuildRow:
    ts: str
    payload_id: str
    payload_name: str
    corr_id: str
    callback_url: str
    domain: str
    path: str
    description: str
    obfuscate: int


@dataclass
class HitRow:
    ts: str
    source: str
    method: str
    client: str
    path: str
    corr_id: str
    payload_id: str
    raw: str


class EngagementStore:
    def __init__(self, name: str, root: Path | None = None) -> None:
        self.name = name
        self.root = root or DEFAULT_ROOT
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / f"{self._safe(name)}.db"
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    @staticmethod
    def _safe(name: str) -> str:
        keep = "-_.abcdefghijklmnopqrstuvwxyz0123456789"
        return "".join(c if c in keep else "_" for c in name.lower()) or "engagement"

    # ---- lifecycle ----------------------------------------------------

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        try:
            yield self._conn
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass

    # ---- meta ---------------------------------------------------------

    def set_meta(self, key: str, value: str) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO meta(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def get_meta(self, key: str, default: str = "") -> str:
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    # ---- builds -------------------------------------------------------

    def record_build(self, *, payload_id: str, payload_name: str,
                     corr_id: str, callback_url: str, domain: str,
                     path: str, description: str = "",
                     obfuscate: int = 0) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO builds(ts, payload_id, payload_name, corr_id, "
                "callback_url, domain, path, description, obfuscate) "
                "VALUES(?,?,?,?,?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"),
                 payload_id, payload_name, corr_id, callback_url,
                 domain, path, description, obfuscate),
            )

    def recent_builds(self, limit: int = 50) -> list[BuildRow]:
        rows = self._conn.execute(
            "SELECT * FROM builds ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [BuildRow(**{k: r[k] for k in r.keys()}) for r in rows]

    def build_for_corr(self, corr_id: str) -> BuildRow | None:
        row = self._conn.execute(
            "SELECT * FROM builds WHERE corr_id = ? ORDER BY id DESC LIMIT 1",
            (corr_id,),
        ).fetchone()
        return BuildRow(**{k: row[k] for k in row.keys()}) if row else None

    def builds_for_payload(self, payload_id: str) -> list[BuildRow]:
        rows = self._conn.execute(
            "SELECT * FROM builds WHERE payload_id = ? ORDER BY id DESC",
            (payload_id,),
        ).fetchall()
        return [BuildRow(**{k: r[k] for k in r.keys()}) for r in rows]

    # ---- hits ---------------------------------------------------------

    def record_hit(self, *, source: str, method: str, client: str,
                   path: str, corr_id: str = "", payload_id: str = "",
                   raw: dict | None = None) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT INTO hits(ts, source, method, client, path, corr_id, "
                "payload_id, raw) VALUES(?,?,?,?,?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"),
                 source, method, client, path, corr_id, payload_id,
                 json.dumps(raw or {}, default=str)),
            )

    def recent_hits(self, limit: int = 200) -> list[HitRow]:
        rows = self._conn.execute(
            "SELECT * FROM hits ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [HitRow(**{k: r[k] for k in r.keys()}) for r in rows]

    def hits_for_corr(self, corr_id: str) -> list[HitRow]:
        rows = self._conn.execute(
            "SELECT * FROM hits WHERE corr_id = ? ORDER BY id DESC",
            (corr_id,),
        ).fetchall()
        return [HitRow(**{k: r[k] for k in r.keys()}) for r in rows]

    # ---- stats --------------------------------------------------------

    def stats(self) -> dict[str, int]:
        b = self._conn.execute("SELECT COUNT(*) AS n FROM builds").fetchone()["n"]
        h = self._conn.execute("SELECT COUNT(*) AS n FROM hits").fetchone()["n"]
        uniq = self._conn.execute(
            "SELECT COUNT(DISTINCT payload_id) AS n FROM hits WHERE payload_id != ''"
        ).fetchone()["n"]
        return {"builds": b, "hits": h, "unique_payloads_hit": uniq}


def list_engagements(root: Path | None = None) -> list[str]:
    root = root or DEFAULT_ROOT
    if not root.exists():
        return []
    return sorted(p.stem for p in root.glob("*.db"))


def export_engagement(store: EngagementStore, out: Path) -> Path:
    """Export an engagement to a JSON bundle.

    Contains metadata, all builds, all hits, and correlation index.
    """
    payload = {
        "name": store.name,
        "created": store.get_meta("created"),
        "callback": store.get_meta("callback"),
        "stats": store.stats(),
        "builds": [b.__dict__ for b in store.recent_builds(limit=10000)],
        "hits": [h.__dict__ for h in store.recent_hits(limit=100000)],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return out