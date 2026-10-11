"""Reusable TUI widgets: banner, status bar, payload table."""
from __future__ import annotations

from rich.text import Text
from textual.widgets import DataTable, Static

from nonpdf import __brand__, __creator__, __version__
from nonpdf.core.registry import registry


BANNER = r"""
    _   _              ___  ____  _____
   | \ | | ___  _ __  |  _ \|  _ \|  ___|
   |  \| |/ _ \| '_ \ | |_) | | | | |_
   | |\  | (_) | | | ||  __/| |_| |  _|
   |_| \_|\___/|_| |_||_|   |____/|_|
"""


class Banner(Static):
    """Fixed brand block used at the top of the dashboard."""

    def render(self) -> Text:
        t = Text()
        t.append(BANNER, style="bold cyan")
        t.append(f"  {__brand__}  ", style="bold white on dark_cyan")
        t.append(f" v{__version__}\n", style="dim")
        t.append(f"  crafted by {__creator__}\n", style="italic cyan")
        t.append("  PDF pentesting cockpit — payloads · obfuscation · listener\n",
                 style="dim")
        return t


class StatusBar(Static):
    """One-line footer strip showing active parameters."""

    def update_status(self, *, callback: str, profile: str,
                      obfuscate: int, hits: int, builds: int) -> None:
        cb = callback or "—"
        t = Text()
        t.append(" callback ", style="bold black on cyan")
        t.append(f" {cb}  ", style="white")
        t.append(" profile ", style="bold black on cyan")
        t.append(f" {profile}  ", style="white")
        t.append(" obfuscate ", style="bold black on cyan")
        t.append(f" L{obfuscate}  ", style="white")
        t.append(" hits ", style="bold black on magenta")
        t.append(f" {hits}  ", style="white")
        t.append(" builds ", style="bold black on green")
        t.append(f" {builds}", style="white")
        self.update(t)


def build_payload_table(platform: str | None = None,
                        tag: str | None = None) -> DataTable:
    """Build a DataTable populated with all registered payloads.

    Columns: ID · Name · Platform · CVE · Tags · Description
    """
    tbl = DataTable(id="payload-table", zebra_stripes=True,
                    cursor_type="row", fixed_columns=1)
    tbl.add_columns("ID", "Name", "Platform", "CVE", "Tags", "Description")
    tags_filter = {tag} if tag else None
    for entry in registry.filter(platform=platform, tags=tags_filter):
        tbl.add_row(
            entry.id,
            entry.name,
            entry.platform,
            entry.cve or "—",
            ",".join(entry.tags) or "—",
            entry.description,
            key=entry.id,
        )
    return tbl