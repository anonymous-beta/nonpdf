from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_binary(path: Path, data: bytes) -> Path:
    ensure_dir(path.parent)
    path.write_bytes(data)
    return path


def write_text(path: Path, text: str) -> Path:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")
    return path
